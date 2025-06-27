from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

# Create your models here.

class RehabilitationPlan(models.Model):
    STATUS_CHOICES = [
        ('active', 'Actif'),
        ('completed', 'Terminé'),
        ('suspended', 'Suspendu'),
        ('cancelled', 'Annulé'),
    ]
    
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='rehabilitation_plans')
    prescribing_doctor = models.ForeignKey('accounts.UserProfile', on_delete=models.SET_NULL, null=True, related_name='prescribed_plans')
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(blank=True, null=True)
    diagnosis = models.TextField(null=True, blank=True)
    goals = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Enhanced functional improvement tracking fields
    baseline_assessment = models.JSONField(
        blank=True, 
        default=dict, 
        help_text="Évaluation initiale des domaines fonctionnels (0-5)"
    )
    expected_duration_weeks = models.PositiveIntegerField(
        default=12, 
        help_text="Durée prévue du plan en semaines"
    )
    family_involvement_score = models.IntegerField(
        default=3,
        help_text="Niveau d'implication familiale (1-5)",
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    target_goals = models.JSONField(
        blank=True,
        default=dict,
        help_text="Objectifs cibles pour chaque domaine fonctionnel"
    )
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        verbose_name = "Plan de réadaptation"
        verbose_name_plural = "Plans de réadaptation"
        ordering = ['-start_date']
    
    def __str__(self):
        return f"Plan de réadaptation pour {self.patient} ({self.start_date})"

class RehabilitationSession(models.Model):
    STATUS_CHOICES = [
        ('planned', 'Planifié'),
        ('completed', 'Terminé'),
        ('cancelled', 'Annulé'),
        ('missed', 'Manqué'),
    ]
    
    SESSION_TYPE_CHOICES = [
        ('physiotherapy', 'Kinésithérapie'),
        ('occupational_therapy', 'Ergothérapie'),
        ('speech_therapy', 'Orthophonie'),
        ('psychological_support', 'Soutien psychologique'),
        ('family_education', 'Éducation familiale'),
        ('group_therapy', 'Thérapie de groupe'),
    ]
    
    rehabilitation_plan = models.ForeignKey(RehabilitationPlan, on_delete=models.CASCADE, related_name='sessions')
    therapist = models.ForeignKey('accounts.UserProfile', on_delete=models.SET_NULL, null=True, related_name='therapy_sessions')
    facility = models.ForeignKey('facilities.Facility', on_delete=models.SET_NULL, null=True)
    session_date = models.DateTimeField(default=timezone.now)
    session_type = models.CharField(
        max_length=50, 
        choices=SESSION_TYPE_CHOICES,
        default='physiotherapy',
        help_text="Type de séance de réhabilitation"
    )
    duration_minutes = models.PositiveIntegerField(default=60)
    notes = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned')
    
    # Enhanced session tracking fields
    exercises_completed = models.JSONField(
        blank=True,
        default=list,
        help_text="Exercices réalisés pendant la séance"
    )
    family_participation = models.BooleanField(
        default=False,
        help_text="Participation de la famille à la séance"
    )
    next_session_recommendations = models.TextField(
        blank=True,
        null=True,
        help_text="Recommandations pour la prochaine séance"
    )
    patient_engagement = models.IntegerField(
        default=3,
        help_text="Niveau d'engagement du patient (1-5)",
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    session_effectiveness = models.IntegerField(
        default=3,
        help_text="Efficacité de la séance (1-5)",
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        verbose_name = "Séance de réadaptation"
        verbose_name_plural = "Séances de réadaptation"
        ordering = ['-session_date']
    
    def __str__(self):
        return f"Séance de {self.session_type or 'réadaptation'} pour {self.rehabilitation_plan.patient} le {self.session_date.strftime('%d/%m/%Y')}"

class RehabilitationAssessment(models.Model):
    rehabilitation_plan = models.ForeignKey(RehabilitationPlan, on_delete=models.CASCADE, related_name='assessments')
    assessor = models.ForeignKey('accounts.UserProfile', on_delete=models.SET_NULL, null=True)
    assessment_date = models.DateField(default=timezone.now)
    findings = models.TextField(null=True, blank=True)
    recommendations = models.TextField(null=True, blank=True)
    attachments = models.FileField(upload_to='rehabilitation/assessments/', blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        verbose_name = "Évaluation de réadaptation"
        verbose_name_plural = "Évaluations de réadaptation"
        ordering = ['-assessment_date']
    
    def __str__(self):
        return f"Évaluation de {self.rehabilitation_plan.patient} le {self.assessment_date}"
