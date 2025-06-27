from django.db import models
from django.utils import timezone

# Create your models here.

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Planifié'),
        ('confirmed', 'Confirmé'),
        ('completed', 'Terminé'),
        ('cancelled', 'Annulé'),
        ('no_show', 'Absence'),
    ]
    
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey('accounts.UserProfile', on_delete=models.CASCADE, related_name='doctor_appointments')
    facility = models.ForeignKey('facilities.Facility', on_delete=models.CASCADE)
    appointment_date = models.DateTimeField(default=timezone.now)
    reason = models.CharField(max_length=200, null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        verbose_name = "Rendez-vous"
        verbose_name_plural = "Rendez-vous"
        ordering = ['-appointment_date']
    
    def __str__(self):
        return f"RDV: {self.patient} avec {self.doctor} le {self.appointment_date.strftime('%d/%m/%Y %H:%M')}"
