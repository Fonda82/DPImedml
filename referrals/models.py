from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User


class Referral(models.Model):
    """
    Patient referral system for Mali healthcare network
    Supports referrals between facilities for specialized care
    """
    
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('accepted', 'Acceptée'),
        ('rejected', 'Refusée'),
        ('completed', 'Complétée'),
        ('cancelled', 'Annulée'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Faible'),
        ('normal', 'Normal'),
        ('high', 'Élevée'),
        ('urgent', 'Urgente'),
    ]
    
    REFERRAL_TYPE_CHOICES = [
        ('consultation', 'Consultation spécialisée'),
        ('rehabilitation', 'Réadaptation'),
        ('surgery', 'Chirurgie'),
        ('diagnostic', 'Diagnostic spécialisé'),
        ('hospitalization', 'Hospitalisation'),
        ('emergency', 'Urgence'),
        ('follow_up', 'Suivi spécialisé'),
    ]
    
    # Core Information
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='referrals')
    referral_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    
    # Facilities
    referring_facility = models.ForeignKey('facilities.Facility', on_delete=models.CASCADE, related_name='outgoing_referrals')
    receiving_facility = models.ForeignKey('facilities.Facility', on_delete=models.CASCADE, related_name='incoming_referrals')
    
    # Medical Staff
    referring_doctor = models.ForeignKey('accounts.UserProfile', on_delete=models.SET_NULL, null=True, related_name='sent_referrals')
    receiving_doctor = models.ForeignKey('accounts.UserProfile', on_delete=models.SET_NULL, null=True, blank=True, related_name='received_referrals')
    
    # Referral Details
    referral_type = models.CharField(max_length=20, choices=REFERRAL_TYPE_CHOICES, default='consultation')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    specialty_requested = models.CharField(max_length=100, verbose_name="Spécialité demandée")
    
    # Medical Information
    reason_for_referral = models.TextField(verbose_name="Motif de référence")
    clinical_summary = models.TextField(verbose_name="Résumé clinique")
    current_diagnosis = models.CharField(max_length=300, blank=True, verbose_name="Diagnostic actuel")
    current_medications = models.TextField(blank=True, verbose_name="Médicaments actuels")
    relevant_history = models.TextField(blank=True, verbose_name="Antécédents pertinents")
    
    # Specific Questions/Requests
    specific_questions = models.TextField(blank=True, verbose_name="Questions spécifiques")
    requested_services = models.TextField(blank=True, verbose_name="Services demandés")
    
    # Urgency and Timing
    preferred_date = models.DateField(null=True, blank=True, verbose_name="Date préférée")
    appointment_deadline = models.DateField(null=True, blank=True, verbose_name="Échéance RDV")
    
    # Status Tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    
    # Response Tracking
    response_date = models.DateTimeField(null=True, blank=True)
    appointment_date = models.DateTimeField(null=True, blank=True, verbose_name="Date RDV confirmée")
    
    # Documentation
    supporting_documents = models.ManyToManyField('patients.Document', blank=True, related_name='referrals')
    
    # Communication
    communication_notes = models.TextField(blank=True, verbose_name="Notes de communication")
    
    class Meta:
        verbose_name = "Référence"
        verbose_name_plural = "Références"
        ordering = ['-created_date']
    
    def __str__(self):
        return f"Référence {self.referral_id} - {self.patient.first_name} {self.patient.last_name} -> {self.receiving_facility.name}"
    
    def save(self, *args, **kwargs):
        if not self.referral_id:
            self.referral_id = self.generate_referral_id()
        super().save(*args, **kwargs)
    
    def generate_referral_id(self):
        """Generate unique referral ID: REF-YYYYMMDD-XXXX"""
        import random
        import string
        from datetime import datetime
        
        date_str = datetime.now().strftime('%Y%m%d')
        random_part = ''.join(random.choices(string.digits, k=4))
        referral_id = f"REF-{date_str}-{random_part}"
        
        # Ensure uniqueness
        while Referral.objects.filter(referral_id=referral_id).exists():
            random_part = ''.join(random.choices(string.digits, k=4))
            referral_id = f"REF-{date_str}-{random_part}"
        
        return referral_id
    
    @property
    def is_urgent(self):
        """Check if referral is urgent priority"""
        return self.priority in ['high', 'urgent']
    
    @property
    def days_pending(self):
        """Calculate days since referral was created"""
        if self.status == 'pending':
            return (timezone.now() - self.created_date).days
        return 0
    
    @property
    def is_overdue(self):
        """Check if referral response is overdue"""
        if self.appointment_deadline and self.status == 'pending':
            return timezone.now().date() > self.appointment_deadline
        return False


class ReferralResponse(models.Model):
    """
    Response from receiving facility to referral request
    """
    
    RESPONSE_TYPE_CHOICES = [
        ('acceptance', 'Acceptation'),
        ('rejection', 'Refus'),
        ('request_info', 'Demande d\'information'),
        ('counter_proposal', 'Contre-proposition'),
        ('partial_acceptance', 'Acceptation partielle'),
    ]
    
    # Core Information
    referral = models.ForeignKey(Referral, on_delete=models.CASCADE, related_name='responses')
    response_type = models.CharField(max_length=20, choices=RESPONSE_TYPE_CHOICES)
    
    # Responder
    responding_doctor = models.ForeignKey('accounts.UserProfile', on_delete=models.SET_NULL, null=True)
    response_date = models.DateTimeField(auto_now_add=True)
    
    # Response Details
    response_message = models.TextField(verbose_name="Message de réponse")
    
    # Acceptance Details (if accepted)
    proposed_appointment_date = models.DateTimeField(null=True, blank=True, verbose_name="Date RDV proposée")
    assigned_doctor = models.ForeignKey('accounts.UserProfile', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_referrals')
    service_location = models.CharField(max_length=200, blank=True, verbose_name="Lieu du service")
    
    # Rejection Details (if rejected)
    rejection_reason = models.TextField(blank=True, verbose_name="Motif de refus")
    alternative_suggestion = models.TextField(blank=True, verbose_name="Suggestion alternative")
    
    # Additional Information Request
    additional_info_needed = models.TextField(blank=True, verbose_name="Informations supplémentaires nécessaires")
    
    # Administrative
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Coût estimé (CFA)")
    expected_duration = models.CharField(max_length=100, blank=True, verbose_name="Durée prévue")
    
    # Follow-up
    follow_up_required = models.BooleanField(default=False, verbose_name="Suivi requis")
    follow_up_instructions = models.TextField(blank=True, verbose_name="Instructions de suivi")
    
    class Meta:
        verbose_name = "Réponse à référence"
        verbose_name_plural = "Réponses aux références"
        ordering = ['-response_date']
    
    def __str__(self):
        return f"Réponse {self.get_response_type_display()} - {self.referral.referral_id}"
    
    def save(self, *args, **kwargs):
        # Update referral status based on response
        super().save(*args, **kwargs)
        
        if self.response_type == 'acceptance':
            self.referral.status = 'accepted'
            self.referral.response_date = self.response_date
            if self.proposed_appointment_date:
                self.referral.appointment_date = self.proposed_appointment_date
            self.referral.receiving_doctor = self.assigned_doctor
        elif self.response_type == 'rejection':
            self.referral.status = 'rejected'
            self.referral.response_date = self.response_date
        
        self.referral.save()


class ReferralFollowUp(models.Model):
    """
    Follow-up tracking for completed referrals
    """
    
    OUTCOME_CHOICES = [
        ('successful', 'Réussi'),
        ('partially_successful', 'Partiellement réussi'),
        ('unsuccessful', 'Non réussi'),
        ('ongoing', 'En cours'),
        ('transferred', 'Transféré ailleurs'),
    ]
    
    # Core Information
    referral = models.OneToOneField(Referral, on_delete=models.CASCADE, related_name='follow_up')
    
    # Follow-up Details
    follow_up_date = models.DateTimeField(auto_now_add=True)
    outcome = models.CharField(max_length=25, choices=OUTCOME_CHOICES, default='ongoing')
    
    # Clinical Outcome
    services_provided = models.TextField(verbose_name="Services fournis")
    diagnosis_confirmation = models.TextField(blank=True, verbose_name="Confirmation diagnostique")
    treatment_provided = models.TextField(blank=True, verbose_name="Traitement fourni")
    
    # Patient Status
    patient_satisfaction = models.PositiveIntegerField(null=True, blank=True, help_text="Note de 1 à 5")
    patient_condition_improved = models.BooleanField(null=True, blank=True, verbose_name="État amélioré")
    
    # Recommendations
    further_referrals_needed = models.BooleanField(default=False, verbose_name="Autres références nécessaires")
    continuing_care_plan = models.TextField(blank=True, verbose_name="Plan de soins continus")
    
    # Feedback
    referring_facility_feedback = models.TextField(blank=True, verbose_name="Commentaires établissement référent")
    receiving_facility_feedback = models.TextField(blank=True, verbose_name="Commentaires établissement receveur")
    
    # Quality Metrics
    timeliness_rating = models.PositiveIntegerField(null=True, blank=True, help_text="Respect des délais (1-5)")
    communication_rating = models.PositiveIntegerField(null=True, blank=True, help_text="Qualité communication (1-5)")
    overall_satisfaction = models.PositiveIntegerField(null=True, blank=True, help_text="Satisfaction globale (1-5)")
    
    # Administrative
    completed_by = models.ForeignKey('accounts.UserProfile', on_delete=models.SET_NULL, null=True)
    completion_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Suivi de référence"
        verbose_name_plural = "Suivis de références"
    
    def __str__(self):
        return f"Suivi {self.referral.referral_id} - {self.get_outcome_display()}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        # Update referral status to completed when follow-up is created
        if self.referral.status != 'completed':
            self.referral.status = 'completed'
            self.referral.save()


class ReferralTemplate(models.Model):
    """
    Templates for common referral types to standardize referrals
    """
    
    name = models.CharField(max_length=200, verbose_name="Nom du modèle")
    referral_type = models.CharField(max_length=20, choices=Referral.REFERRAL_TYPE_CHOICES)
    specialty = models.CharField(max_length=100, verbose_name="Spécialité")
    
    # Template Fields
    template_reason = models.TextField(verbose_name="Motif type")
    template_questions = models.TextField(blank=True, verbose_name="Questions standard")
    required_documents = models.TextField(blank=True, verbose_name="Documents requis")
    preparation_instructions = models.TextField(blank=True, verbose_name="Instructions de préparation")
    
    # Usage
    created_by = models.ForeignKey('accounts.UserProfile', on_delete=models.SET_NULL, null=True)
    created_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    usage_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = "Modèle de référence"
        verbose_name_plural = "Modèles de références"
        ordering = ['specialty', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.specialty}"
