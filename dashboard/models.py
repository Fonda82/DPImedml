from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

# Create your models here.

class SystemActivity(models.Model):
    ACTION_TYPES = [
        ('login', 'Login'),
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('register', 'Register'),
        ('export', 'Data Export'),
        ('access', 'Data Access'),
        ('other', 'Other'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    action = models.CharField(max_length=100)
    description = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES, default='other')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = "System Activity"
        verbose_name_plural = "System Activities"
    
    def __str__(self):
        return f"{self.action} - {self.timestamp}"

class SecurityAudit(models.Model):
    AUDIT_TYPES = [
        ('login_failed', 'Failed Login'),
        ('login_success', 'Successful Login'),
        ('password_change', 'Password Change'),
        ('data_access', 'Data Access'),
        ('permission_change', 'Permission Change'),
        ('account_locked', 'Account Locked'),
        ('gdpr_request', 'GDPR Request'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    audit_type = models.CharField(max_length=30, choices=AUDIT_TYPES)
    description = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    risk_level = models.CharField(max_length=10, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ], default='low')
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Security Audit"
        verbose_name_plural = "Security Audits"

class LoginAttempt(models.Model):
    username = models.CharField(max_length=150)
    ip_address = models.GenericIPAddressField()
    success = models.BooleanField()
    timestamp = models.DateTimeField(default=timezone.now)
    user_agent = models.TextField(null=True, blank=True)
    failure_reason = models.CharField(max_length=100, null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']

class PatientConsent(models.Model):
    CONSENT_TYPES = [
        ('data_processing', 'Data Processing'),
        ('medical_records', 'Medical Records'),
        ('sharing_partners', 'Data Sharing with Partners'),
        ('marketing', 'Marketing Communications'),
        ('research', 'Medical Research'),
    ]
    
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='consents')
    consent_type = models.CharField(max_length=30, choices=CONSENT_TYPES)
    granted = models.BooleanField()
    granted_at = models.DateTimeField(default=timezone.now)
    granted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='granted_consents')
    revoked_at = models.DateTimeField(null=True, blank=True)
    revoked_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='revoked_consents')
    legal_basis = models.TextField(help_text="Legal basis for processing (GDPR Article 6)")
    
    class Meta:
        ordering = ['-granted_at']
        verbose_name = "Patient Consent"
        verbose_name_plural = "Patient Consents"

class DataRetentionPolicy(models.Model):
    DATA_TYPES = [
        ('medical_records', 'Medical Records'),
        ('appointment_history', 'Appointment History'),
        ('voucher_data', 'Voucher Data'),
        ('rehabilitation_plans', 'Rehabilitation Plans'),
        ('system_logs', 'System Logs'),
    ]
    
    data_type = models.CharField(max_length=30, choices=DATA_TYPES, unique=True)
    retention_period_days = models.IntegerField(help_text="Number of days to retain data")
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Data Retention Policy"
        verbose_name_plural = "Data Retention Policies"
