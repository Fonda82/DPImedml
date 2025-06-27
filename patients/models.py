from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.utils import timezone
import uuid
import hashlib
from django.utils import timezone
import random
import string
from datetime import datetime

class Patient(models.Model):
    GENDER_CHOICES = [
        ('M', 'Masculin'),
        ('F', 'Féminin'),
        ('O', 'Autre'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    patient_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    first_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    region = models.CharField(max_length=100, null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    # Guardian information
    guardian_name = models.CharField(max_length=200, null=True, blank=True)
    guardian_relationship = models.CharField(max_length=50, null=True, blank=True)
    guardian_phone = models.CharField(max_length=20, null=True, blank=True) 
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.patient_id})"
    
    def save(self, *args, **kwargs):
        # Generate unique patient ID if not already set
        if not self.patient_id:
            self.patient_id = self.generate_patient_id()
        super().save(*args, **kwargs)
    
    def generate_patient_id(self):
        """
        Generate unique patient ID based on patient traits per TDR.md requirements.
        Format: P-[first 2 letters of last name][first letter of first name][birthyear last 2 digits]-[random 4 digits]
        """
        # Get initials from name
        last_name_str = str(self.last_name) if self.last_name else "XX"
        first_name_str = str(self.first_name) if self.first_name else "X"
        
        last_initial = last_name_str[:2].upper()
        first_initial = first_name_str[:1].upper()
        
        # Get year of birth if available
        birth_year = "00"
        if self.date_of_birth:
            # Handle both datetime objects and string dates
            if isinstance(self.date_of_birth, str):
                try:
                    date_obj = datetime.strptime(self.date_of_birth, '%Y-%m-%d')
                    birth_year = str(date_obj.year)[-2:]
                except ValueError:
                    birth_year = "00"
            else:
                birth_year = str(self.date_of_birth.year)[-2:]
        
        # Generate random component
        random_part = ''.join(random.choices(string.digits, k=4))
        
        # Combine to create ID
        patient_id = f"P-{last_initial}{first_initial}{birth_year}-{random_part}"
        
        # Check uniqueness and regenerate if needed
        duplicate_count = 0
        while Patient.objects.filter(patient_id=patient_id).exists():
            random_part = ''.join(random.choices(string.digits, k=4))
            patient_id = f"P-{last_initial}{first_initial}{birth_year}-{random_part}"
            duplicate_count += 1
            if duplicate_count > 10:  # Avoid infinite loop
                break
        
        return patient_id

class ICD10Code(models.Model):
    """
    ICD-10 diagnostic codes with focus on pediatric disabilities and common conditions in Mali
    """
    CATEGORY_CHOICES = [
        ('F00-F99', 'Troubles mentaux et du comportement'),
        ('G00-G99', 'Maladies du système nerveux'),
        ('H00-H59', 'Maladies de l\'œil et de ses annexes'),
        ('H60-H95', 'Maladies de l\'oreille et de l\'apophyse mastoïde'),
        ('Q00-Q99', 'Malformations congénitales'),
        ('R00-R99', 'Symptômes et signes anormaux'),
        ('Z00-Z99', 'Facteurs influençant l\'état de santé'),
        ('OTHER', 'Autres'),
    ]
    
    code = models.CharField(max_length=10, unique=True, help_text="Code ICD-10 (ex: F84.0)")
    title = models.CharField(max_length=200, help_text="Titre officiel du diagnostic")
    description = models.TextField(blank=True, help_text="Description détaillée du diagnostic")
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES, default='OTHER')
    is_pediatric_relevant = models.BooleanField(default=False, help_text="Pertinent pour la pédiatrie (0-14 ans)")
    is_disability_related = models.BooleanField(default=False, help_text="Lié aux handicaps")
    is_common_in_mali = models.BooleanField(default=False, help_text="Fréquent au Mali")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Code ICD-10"
        verbose_name_plural = "Codes ICD-10"
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.title}"

class MedicalRecord(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    doctor = models.ForeignKey('accounts.UserProfile', on_delete=models.SET_NULL, null=True, related_name='medical_records')
    facility = models.ForeignKey('facilities.Facility', on_delete=models.SET_NULL, null=True)
    date = models.DateTimeField(null=True, blank=True)
    
    # ICD-10 Professional Diagnostic Coding
    primary_diagnosis_icd10 = models.ForeignKey(
        ICD10Code, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='primary_diagnoses',
        help_text="Diagnostic principal (ICD-10)"
    )
    secondary_diagnoses_icd10 = models.ManyToManyField(
        ICD10Code,
        blank=True,
        related_name='secondary_diagnoses',
        help_text="Diagnostics secondaires (ICD-10)"
    )
    
    # Legacy diagnosis field (for backward compatibility)
    diagnosis = models.CharField(max_length=200, null=True, blank=True, help_text="Diagnostic (texte libre - legacy)")
    
    # Clinical details
    chief_complaint = models.TextField(null=True, blank=True, help_text="Motif de consultation")
    present_illness = models.TextField(null=True, blank=True, help_text="Histoire de la maladie actuelle")
    physical_examination = models.TextField(null=True, blank=True, help_text="Examen physique")
    clinical_notes = models.TextField(null=True, blank=True, help_text="Notes cliniques")
    
    # Treatment and recommendations
    description = models.TextField(null=True, blank=True, help_text="Description générale")
    treatment_plan = models.TextField(null=True, blank=True, help_text="Plan de traitement")
    recommendations = models.TextField(blank=True, null=True, help_text="Recommandations")
    follow_up_instructions = models.TextField(null=True, blank=True, help_text="Instructions de suivi")
    
    # Administrative
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        verbose_name = "Dossier médical"
        verbose_name_plural = "Dossiers médicaux"
        ordering = ['-date']
    
    def __str__(self):
        date_str = self.date.strftime('%Y-%m-%d %H:%M') if self.date else 'No date'
        primary_dx = self.primary_diagnosis_icd10.code if self.primary_diagnosis_icd10 else (self.diagnosis or 'No diagnosis')
        return f"{self.patient} - {primary_dx} ({date_str})"
    
    def get_all_diagnoses(self):
        """Return all diagnoses (primary + secondary) for this record"""
        diagnoses = []
        if self.primary_diagnosis_icd10:
            diagnoses.append(self.primary_diagnosis_icd10)
        diagnoses.extend(list(self.secondary_diagnoses_icd10.all()))
        return diagnoses

class VitalSigns(models.Model):
    """
    Vital signs with pediatric focus for children 0-14 years
    """
    medical_record = models.OneToOneField(MedicalRecord, on_delete=models.CASCADE, related_name='vital_signs')
    
    # Basic vital signs
    temperature = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True, help_text="Température (°C)")
    heart_rate = models.PositiveIntegerField(null=True, blank=True, help_text="Fréquence cardiaque (bpm)")
    respiratory_rate = models.PositiveIntegerField(null=True, blank=True, help_text="Fréquence respiratoire (/min)")
    systolic_bp = models.PositiveIntegerField(null=True, blank=True, help_text="Tension systolique (mmHg)")
    diastolic_bp = models.PositiveIntegerField(null=True, blank=True, help_text="Tension diastolique (mmHg)")
    oxygen_saturation = models.PositiveIntegerField(null=True, blank=True, help_text="Saturation O2 (%)")
    
    # Pediatric measurements
    height = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True, help_text="Taille (cm)")
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Poids (kg)")
    head_circumference = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True, help_text="Périmètre crânien (cm)")
    bmi = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True, help_text="IMC (calculé)")
    
    # Growth percentiles (calculated)
    height_percentile = models.PositiveIntegerField(null=True, blank=True, help_text="Percentile taille")
    weight_percentile = models.PositiveIntegerField(null=True, blank=True, help_text="Percentile poids")
    bmi_percentile = models.PositiveIntegerField(null=True, blank=True, help_text="Percentile IMC")
    
    # Nutritional status
    NUTRITIONAL_STATUS_CHOICES = [
        ('UNDERWEIGHT', 'Insuffisance pondérale'),
        ('NORMAL', 'Normal'),
        ('OVERWEIGHT', 'Surpoids'),
        ('OBESITY', 'Obésité'),
        ('SEVERE_MALNUTRITION', 'Malnutrition sévère'),
        ('MODERATE_MALNUTRITION', 'Malnutrition modérée'),
    ]
    nutritional_status = models.CharField(max_length=25, choices=NUTRITIONAL_STATUS_CHOICES, null=True, blank=True)
    
    # Additional pediatric assessments
    developmental_milestones_appropriate = models.BooleanField(null=True, blank=True, help_text="Jalons développementaux appropriés")
    notes = models.TextField(null=True, blank=True, help_text="Notes sur les signes vitaux")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Signes vitaux"
        verbose_name_plural = "Signes vitaux"
    
    def save(self, *args, **kwargs):
        # Auto-calculate BMI if height and weight are available
        if self.height and self.weight and self.height > 0:
            height_m = float(self.height) / 100  # Convert cm to meters
            self.bmi = round(float(self.weight) / (height_m ** 2), 1)
        
        # Calculate nutritional status based on BMI and age (simplified)
        if self.bmi:
            patient_age = self.get_patient_age()
            if patient_age:
                if self.bmi < 16:
                    self.nutritional_status = 'SEVERE_MALNUTRITION'
                elif self.bmi < 18.5:
                    self.nutritional_status = 'UNDERWEIGHT'
                elif self.bmi < 25:
                    self.nutritional_status = 'NORMAL'
                elif self.bmi < 30:
                    self.nutritional_status = 'OVERWEIGHT'
                else:
                    self.nutritional_status = 'OBESITY'
        
        super().save(*args, **kwargs)
    
    def get_patient_age(self):
        """Calculate patient age in years"""
        if self.medical_record.patient.date_of_birth and self.medical_record.date:
            birth_date = self.medical_record.patient.date_of_birth
            record_date = self.medical_record.date.date()
            age = record_date.year - birth_date.year
            if record_date.month < birth_date.month or (record_date.month == birth_date.month and record_date.day < birth_date.day):
                age -= 1
            return age
        return None
    
    def get_blood_pressure_display(self):
        """Return formatted blood pressure"""
        if self.systolic_bp and self.diastolic_bp:
            return f"{self.systolic_bp}/{self.diastolic_bp}"
        return None
    
    def __str__(self):
        return f"Signes vitaux - {self.medical_record.patient} ({self.medical_record.date.strftime('%d/%m/%Y') if self.medical_record.date else 'No date'})"

class Document(models.Model):
    CATEGORY_CHOICES = [
        ('REPORT', 'Rapport'),
        ('PRESCRIPTION', 'Prescription'),
        ('IMAGING', 'Imagerie'),
        ('LAB', 'Laboratoire'),
        ('OTHER', 'Autre'),
    ]
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='OTHER')
    description = models.TextField(null=True, blank=True)
    file = models.FileField(upload_to='patients/documents/')
    file_type = models.CharField(max_length=20, null=True, blank=True)
    uploaded_by = models.ForeignKey('accounts.UserProfile', on_delete=models.SET_NULL, null=True, related_name='uploaded_documents')
    upload_date = models.DateTimeField(default=timezone.now)
    document_date = models.DateField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Document médical"
        verbose_name_plural = "Documents médicaux"
        ordering = ['-upload_date']
    
    def __str__(self):
        return f"{self.title} - {self.patient}"
    
    def save(self, *args, **kwargs):
        # Determine file type based on extension
        if self.file:
            filename = self.file.name.lower()
            if filename.endswith('.pdf'):
                self.file_type = 'pdf'
            elif filename.endswith(('.jpg', '.jpeg', '.png', '.gif')):
                self.file_type = 'image'
            elif filename.endswith(('.doc', '.docx')):
                self.file_type = 'doc'
            elif filename.endswith(('.xls', '.xlsx')):
                self.file_type = 'xls'
            else:
                self.file_type = 'other'
        super().save(*args, **kwargs)

class RehabilitationExercise(models.Model):
    DIFFICULTY_CHOICES = [
        ('beginner', 'Débutant'),
        ('intermediate', 'Intermédiaire'),
        ('advanced', 'Avancé'),
        ('expert', 'Expert'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    difficulty_level = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='beginner')
    duration_minutes = models.PositiveIntegerField()
    instructions = models.TextField()
    precautions = models.TextField(blank=True)
    equipment_needed = models.CharField(max_length=200, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['difficulty_level', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_difficulty_level_display()})"

# ========================================
# HOSPITALIZATION MODULE - TDR REQUIREMENT
# ========================================

class Hospitalization(models.Model):
    STATUS_CHOICES = [
        ('admitted', 'Hospitalisé'),
        ('discharged', 'Sorti'),
        ('transferred', 'Transféré'),
        ('deceased', 'Décédé'),
    ]
    
    ROOM_CHOICES = [
        ('pediatrie_A', 'Pavillon Pédiatrique A'),
        ('pediatrie_B', 'Pavillon Pédiatrique B'),
        ('readaptation', 'Unité de Réadaptation'),
        ('urgences', 'Service des Urgences'),
        ('chirurgie', 'Chirurgie Pédiatrique'),
        ('soins_intensifs', 'Soins Intensifs'),
    ]
    
    # Core Information
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='hospitalizations')
    admission_date = models.DateTimeField()
    discharge_date = models.DateTimeField(null=True, blank=True)
    
    # Medical Staff
    admitting_doctor = models.ForeignKey('accounts.UserProfile', on_delete=models.SET_NULL, null=True, related_name='admissions')
    attending_doctor = models.ForeignKey('accounts.UserProfile', on_delete=models.SET_NULL, null=True, related_name='attended_patients')
    
    # Admission Details
    admission_reason = models.TextField(verbose_name="Motif d'admission")
    admission_diagnosis = models.CharField(max_length=500, verbose_name="Diagnostic d'admission")
    
    # Location
    room_number = models.CharField(max_length=20, choices=ROOM_CHOICES, verbose_name="Chambre/Service")
    bed_number = models.CharField(max_length=10, verbose_name="Lit numéro")
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='admitted')
    
    # Discharge Information
    discharge_diagnosis = models.TextField(blank=True, verbose_name="Diagnostic de sortie")
    discharge_summary = models.TextField(blank=True, verbose_name="Résumé de sortie")
    
    # Timestamps
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-admission_date']
        verbose_name = "Hospitalisation"
        verbose_name_plural = "Hospitalisations"
    
    def __str__(self):
        return f"Hospitalisation - {self.patient.first_name} {self.patient.last_name} ({self.admission_date.strftime('%d/%m/%Y') if self.admission_date else 'Date inconnue'})"
    
    @property
    def duration_days(self):
        """Calculate length of stay"""
        if not self.admission_date:
            return 0
        end_date = self.discharge_date or timezone.now()
        return (end_date - self.admission_date).days
    
    @property
    def is_active(self):
        """Check if patient is currently hospitalized"""
        return self.status == 'admitted' and self.discharge_date is None


class HospitalizationProgressNote(models.Model):
    SHIFT_CHOICES = [
        ('morning', 'Matin (6h-14h)'),
        ('afternoon', 'Après-midi (14h-22h)'),
        ('night', 'Nuit (22h-6h)'),
    ]
    
    # Core Information
    hospitalization = models.ForeignKey(Hospitalization, on_delete=models.CASCADE, related_name='progress_notes')
    date = models.DateField()
    time = models.TimeField()
    shift = models.CharField(max_length=20, choices=SHIFT_CHOICES, default='morning')
    
    # Author
    author = models.ForeignKey('accounts.UserProfile', on_delete=models.SET_NULL, null=True)
    
    # Clinical Notes
    progress_note = models.TextField(verbose_name="Note d'évolution")
    treatment_administered = models.TextField(blank=True, verbose_name="Traitements administrés")
    complications = models.TextField(blank=True, verbose_name="Complications observées")
    
    # Vital Signs (for pediatric patients)
    temperature = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True, verbose_name="Température (°C)")
    heart_rate = models.PositiveIntegerField(null=True, blank=True, verbose_name="Fréquence cardiaque (bpm)")
    respiratory_rate = models.PositiveIntegerField(null=True, blank=True, verbose_name="Fréquence respiratoire")
    blood_pressure_systolic = models.PositiveIntegerField(null=True, blank=True, verbose_name="TA systolique")
    blood_pressure_diastolic = models.PositiveIntegerField(null=True, blank=True, verbose_name="TA diastolique")
    oxygen_saturation = models.PositiveIntegerField(null=True, blank=True, verbose_name="Saturation O2 (%)")
    weight = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True, verbose_name="Poids (kg)")
    
    # Additional Fields
    family_visit = models.BooleanField(default=False, verbose_name="Visite famille")
    family_notes = models.TextField(blank=True, verbose_name="Notes famille/tuteur")
    
    # Timestamps
    created_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date', '-time']
        verbose_name = "Note d'évolution"
        verbose_name_plural = "Notes d'évolution"
    
    def __str__(self):
        date_str = self.date.strftime('%d/%m/%Y') if self.date else 'Date inconnue'
        return f"Note {date_str} - {self.shift} - {self.hospitalization.patient.first_name} {self.hospitalization.patient.last_name}"


class DischargeReport(models.Model):
    DISCHARGE_TYPE_CHOICES = [
        ('home', 'Retour à domicile'),
        ('transfer', 'Transfert vers autre établissement'),
        ('against_advice', 'Sortie contre avis médical'),
        ('deceased', 'Décès'),
        ('rehabilitation', 'Centre de réadaptation'),
    ]
    
    CONDITION_CHOICES = [
        ('improved', 'Amélioré'),
        ('stable', 'Stable'),
        ('worsened', 'Aggravé'),
        ('cured', 'Guéri'),
        ('chronic', 'Chronique stabilisé'),
    ]
    
    # Core Information
    hospitalization = models.OneToOneField(Hospitalization, on_delete=models.CASCADE, related_name='discharge_report')
    
    # Discharge Details
    discharge_type = models.CharField(max_length=20, choices=DISCHARGE_TYPE_CHOICES, verbose_name="Type de sortie")
    discharge_condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, verbose_name="État à la sortie")
    final_diagnosis = models.TextField(verbose_name="Diagnostic final")
    
    # Treatment Summary
    treatment_summary = models.TextField(verbose_name="Résumé des traitements")
    procedures_performed = models.TextField(blank=True, verbose_name="Procédures réalisées")
    complications_during_stay = models.TextField(blank=True, verbose_name="Complications pendant le séjour")
    
    # Follow-up Instructions
    follow_up_instructions = models.TextField(verbose_name="Instructions de suivi")
    medications_at_discharge = models.TextField(blank=True, verbose_name="Médicaments à la sortie")
    next_appointment_date = models.DateField(null=True, blank=True, verbose_name="Prochain RDV")
    next_appointment_service = models.CharField(max_length=200, blank=True, verbose_name="Service de suivi")
    
    # Transfer Information (if applicable)
    transfer_facility = models.ForeignKey('facilities.Facility', on_delete=models.SET_NULL, null=True, blank=True, 
                                        verbose_name="Établissement de transfert")
    transfer_reason = models.TextField(blank=True, verbose_name="Motif de transfert")
    
    # Family/Guardian Information
    family_education_provided = models.BooleanField(default=False, verbose_name="Éducation famille fournie")
    family_education_notes = models.TextField(blank=True, verbose_name="Notes éducation famille")
    
    # Rehabilitation Specific
    rehabilitation_goals_achieved = models.TextField(blank=True, verbose_name="Objectifs de réadaptation atteints")
    home_exercise_program = models.TextField(blank=True, verbose_name="Programme d'exercices à domicile")
    assistive_devices_provided = models.CharField(max_length=500, blank=True, verbose_name="Aides techniques fournies")
    
    # Administrative
    discharge_prepared_by = models.ForeignKey('accounts.UserProfile', on_delete=models.SET_NULL, null=True)
    report_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Rapport de sortie"
        verbose_name_plural = "Rapports de sortie"
    
    def __str__(self):
        report_date_str = self.report_date.strftime('%d/%m/%Y') if self.report_date else 'Date inconnue'
        return f"Rapport de sortie - {self.hospitalization.patient.first_name} {self.hospitalization.patient.last_name} ({report_date_str})"
