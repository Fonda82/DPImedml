from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from patients.models import Patient
from accounts.models import UserProfile
from facilities.models import Facility
import uuid

class MedicationCategory(models.Model):
    """
    Categories of medications commonly used in pediatric care in Mali
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    color_code = models.CharField(max_length=7, default='#0C7C59')  # Mali green
    icon = models.CharField(max_length=50, default='fa-pills')
    
    class Meta:
        verbose_name = "Catégorie de médicament"
        verbose_name_plural = "Catégories de médicaments"
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Medication(models.Model):
    """
    Medication database with pediatric focus for Mali healthcare context
    """
    FORM_CHOICES = [
        ('TABLET', 'Comprimé'),
        ('CAPSULE', 'Gélule'),
        ('SYRUP', 'Sirop'),
        ('SUSPENSION', 'Suspension'),
        ('INJECTION', 'Injection'),
        ('CREAM', 'Crème'),
        ('OINTMENT', 'Pommade'),
        ('DROPS', 'Gouttes'),
        ('INHALER', 'Inhalateur'),
        ('POWDER', 'Poudre'),
        ('OTHER', 'Autre'),
    ]
    
    STORAGE_CHOICES = [
        ('ROOM_TEMP', 'Température ambiante'),
        ('COOL', 'Endroit frais'),
        ('REFRIGERATED', 'Réfrigéré'),
        ('FREEZER', 'Congelé'),
        ('DRY', 'Endroit sec'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=200, help_text="Nom commercial du médicament")
    generic_name = models.CharField(max_length=200, help_text="Dénomination commune internationale (DCI)")
    category = models.ForeignKey(MedicationCategory, on_delete=models.SET_NULL, null=True)
    manufacturer = models.CharField(max_length=200, blank=True)
    
    # Formulation
    form = models.CharField(max_length=20, choices=FORM_CHOICES, default='TABLET')
    strength = models.CharField(max_length=100, help_text="ex: 250mg, 5ml, 100mg/5ml")
    unit = models.CharField(max_length=50, help_text="mg, ml, UI, etc.")
    
    # Pediatric Information
    is_pediatric_approved = models.BooleanField(default=True, help_text="Approuvé pour usage pédiatrique")
    min_age_months = models.PositiveIntegerField(null=True, blank=True, help_text="Âge minimum en mois")
    max_age_years = models.PositiveIntegerField(null=True, blank=True, help_text="Âge maximum en années")
    weight_based_dosing = models.BooleanField(default=True, help_text="Dosage basé sur le poids")
    
    # Dosing Guidelines
    default_dose_per_kg = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True, 
                                            help_text="Dose par kg de poids corporel")
    max_dose_per_day = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True,
                                         help_text="Dose maximale par jour")
    frequency_per_day = models.PositiveIntegerField(default=1, help_text="Fréquence par jour")
    
    # Safety Information
    contraindications = models.TextField(blank=True, help_text="Contre-indications")
    side_effects = models.TextField(blank=True, help_text="Effets secondaires")
    drug_interactions = models.TextField(blank=True, help_text="Interactions médicamenteuses")
    pregnancy_category = models.CharField(max_length=2, blank=True, help_text="Catégorie grossesse")
    
    # Mali Context
    available_in_mali = models.BooleanField(default=True, help_text="Disponible au Mali")
    essential_drug_list = models.BooleanField(default=False, help_text="Liste des médicaments essentiels")
    requires_special_storage = models.CharField(max_length=20, choices=STORAGE_CHOICES, default='ROOM_TEMP')
    
    # Administrative
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name = "Médicament"
        verbose_name_plural = "Médicaments"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.strength})"
    
    def get_pediatric_dose(self, weight_kg, age_months):
        """
        Calculate pediatric dose based on weight and age
        """
        if not self.is_pediatric_approved:
            return None
            
        if self.min_age_months and age_months < self.min_age_months:
            return None
            
        if self.max_age_years and age_months > (self.max_age_years * 12):
            return None
            
        if self.weight_based_dosing and self.default_dose_per_kg and weight_kg:
            calculated_dose = float(self.default_dose_per_kg) * weight_kg
            
            # Check maximum dose
            if self.max_dose_per_day and calculated_dose > float(self.max_dose_per_day):
                calculated_dose = float(self.max_dose_per_day)
                
            return {
                'dose': round(calculated_dose, 2),
                'frequency': self.frequency_per_day,
                'unit': self.unit,
                'form': self.get_form_display()
            }
        
        return None

class Prescription(models.Model):
    """
    Electronic prescription system for pediatric patients
    """
    STATUS_CHOICES = [
        ('DRAFT', 'Brouillon'),
        ('PRESCRIBED', 'Prescrit'),
        ('VALIDATED', 'Validé'),
        ('DISPENSED', 'Délivré'),
        ('COMPLETED', 'Terminé'),
        ('CANCELLED', 'Annulé'),
        ('EXPIRED', 'Expiré'),
    ]
    
    PRIORITY_CHOICES = [
        ('LOW', 'Faible'),
        ('NORMAL', 'Normal'),
        ('HIGH', 'Élevé'),
        ('URGENT', 'Urgent'),
    ]
    
    # Identification
    prescription_id = models.CharField(max_length=20, unique=True, blank=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='prescriptions')
    medical_record = models.ForeignKey('patients.MedicalRecord', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Healthcare Providers
    prescribing_doctor = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, 
                                         related_name='prescribed_prescriptions')
    validating_pharmacist = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True,
                                            related_name='validated_prescriptions')
    dispensing_pharmacist = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True,
                                            related_name='dispensed_prescriptions')
    
    # Facilities
    prescribing_facility = models.ForeignKey(Facility, on_delete=models.SET_NULL, null=True,
                                           related_name='prescriptions_issued')
    dispensing_facility = models.ForeignKey(Facility, on_delete=models.SET_NULL, null=True, blank=True,
                                          related_name='prescriptions_dispensed')
    
    # Prescription Details
    diagnosis = models.CharField(max_length=500, help_text="Diagnostic associé")
    clinical_notes = models.TextField(blank=True, help_text="Notes cliniques")
    instructions = models.TextField(blank=True, help_text="Instructions pour le patient")
    
    # Status and Priority
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='NORMAL')
    
    # Dates
    prescribed_date = models.DateTimeField(default=timezone.now)
    validated_date = models.DateTimeField(null=True, blank=True)
    dispensed_date = models.DateTimeField(null=True, blank=True)
    expiry_date = models.DateTimeField(null=True, blank=True)
    
    # Mali Healthcare Workflow
    requires_authorization = models.BooleanField(default=False, help_text="Nécessite autorisation spéciale")
    covered_by_insurance = models.BooleanField(default=False, help_text="Couvert par assurance")
    voucher_required = models.BooleanField(default=False, help_text="Bon de prise en charge requis")
    
    # Administrative
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Prescription"
        verbose_name_plural = "Prescriptions"
        ordering = ['-prescribed_date']
    
    def save(self, *args, **kwargs):
        # Generate prescription ID if not set
        if not self.prescription_id:
            self.prescription_id = self.generate_prescription_id()
        
        # Set expiry date (30 days from prescription)
        if not self.expiry_date:
            from datetime import timedelta
            self.expiry_date = self.prescribed_date + timedelta(days=30)
        
        super().save(*args, **kwargs)
    
    def generate_prescription_id(self):
        """Generate unique prescription ID: RX-YYYYMMDD-XXXX"""
        from datetime import datetime
        import random
        import string
        
        date_str = datetime.now().strftime('%Y%m%d')
        random_str = ''.join(random.choices(string.digits, k=4))
        prescription_id = f"RX-{date_str}-{random_str}"
        
        # Ensure uniqueness
        while Prescription.objects.filter(prescription_id=prescription_id).exists():
            random_str = ''.join(random.choices(string.digits, k=4))
            prescription_id = f"RX-{date_str}-{random_str}"
        
        return prescription_id
    
    def __str__(self):
        return f"{self.prescription_id} - {self.patient.first_name} {self.patient.last_name}"
    
    def get_total_medications(self):
        """Get total number of medications in this prescription"""
        return self.prescriptionmedication_set.count()
    
    def is_expired(self):
        """Check if prescription is expired"""
        return self.expiry_date and timezone.now() > self.expiry_date

class PrescriptionMedication(models.Model):
    """
    Through model for prescription medications with detailed dosing instructions
    """
    ROUTE_CHOICES = [
        ('ORAL', 'Voie orale'),
        ('TOPICAL', 'Voie topique'),
        ('INJECTION', 'Injection'),
        ('INHALATION', 'Inhalation'),
        ('NASAL', 'Voie nasale'),
        ('OPHTHALMIC', 'Voie ophtalmique'),
        ('OTIC', 'Voie auriculaire'),
        ('RECTAL', 'Voie rectale'),
        ('OTHER', 'Autre'),
    ]
    
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE)
    medication = models.ForeignKey(Medication, on_delete=models.CASCADE)
    
    # Dosing Information
    dose = models.DecimalField(max_digits=10, decimal_places=3, help_text="Dose par prise")
    dose_unit = models.CharField(max_length=20, help_text="Unité de dose (mg, ml, etc.)")
    frequency = models.CharField(max_length=100, help_text="Fréquence (ex: 3 fois par jour)")
    route = models.CharField(max_length=20, choices=ROUTE_CHOICES, default='ORAL')
    
    # Duration
    duration_days = models.PositiveIntegerField(help_text="Durée du traitement en jours")
    total_quantity = models.DecimalField(max_digits=10, decimal_places=2, 
                                       help_text="Quantité totale à délivrer")
    
    # Instructions
    instructions = models.TextField(help_text="Instructions spécifiques (avant/après repas, etc.)")
    special_notes = models.TextField(blank=True, help_text="Notes spéciales")
    
    # Substitution
    substitution_allowed = models.BooleanField(default=True, help_text="Substitution générique autorisée")
    
    # Tracking
    dispensed_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0,
                                           help_text="Quantité déjà délivrée")
    is_dispensed = models.BooleanField(default=False)
    dispensed_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Médicament prescrit"
        verbose_name_plural = "Médicaments prescrits"
    
    def __str__(self):
        return f"{self.medication.name} - {self.dose} {self.dose_unit}"
    
    def get_daily_dose(self):
        """Calculate total daily dose"""
        # Extract numeric frequency (simplified)
        try:
            freq_num = int(''.join(filter(str.isdigit, self.frequency)))
            return float(self.dose) * freq_num
        except:
            return float(self.dose)
    
    def is_fully_dispensed(self):
        """Check if medication is fully dispensed"""
        return self.dispensed_quantity >= self.total_quantity

class PrescriptionTemplate(models.Model):
    """
    Common prescription templates for Mali pediatric healthcare
    """
    name = models.CharField(max_length=200, help_text="Nom du protocole")
    description = models.TextField(help_text="Description du protocole")
    category = models.ForeignKey(MedicationCategory, on_delete=models.SET_NULL, null=True)
    
    # Applicability
    min_age_months = models.PositiveIntegerField(null=True, blank=True)
    max_age_months = models.PositiveIntegerField(null=True, blank=True)
    conditions = models.TextField(help_text="Conditions d'application")
    
    # Template Content
    medications = models.ManyToManyField(Medication, through='TemplateMedication')
    standard_instructions = models.TextField(blank=True)
    
    # Mali Context
    is_who_approved = models.BooleanField(default=False, help_text="Approuvé par l'OMS")
    is_mali_standard = models.BooleanField(default=False, help_text="Standard au Mali")
    
    created_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Protocole de prescription"
        verbose_name_plural = "Protocoles de prescription"
        ordering = ['name']
    
    def __str__(self):
        return self.name

class TemplateMedication(models.Model):
    """
    Medications in prescription templates with standard dosing
    """
    template = models.ForeignKey(PrescriptionTemplate, on_delete=models.CASCADE)
    medication = models.ForeignKey(Medication, on_delete=models.CASCADE)
    
    # Standard Dosing
    standard_dose_per_kg = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    standard_frequency = models.CharField(max_length=100, default="2 fois par jour")
    standard_duration = models.PositiveIntegerField(default=7, help_text="Durée standard en jours")
    standard_instructions = models.TextField(blank=True)
    
    # Priority in template
    order = models.PositiveIntegerField(default=1)
    is_optional = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['order']
