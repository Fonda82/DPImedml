from django.db import models
import uuid
import qrcode
from io import BytesIO
from django.core.files import File
from PIL import Image, ImageDraw
from django.utils import timezone
from datetime import timedelta

def get_default_expiry():
    return timezone.now().date() + timedelta(days=90)

class Voucher(models.Model):
    STATUS_CHOICES = [
        ('issued', 'Émis'),
        ('validated', 'Validé'),
        ('used', 'Utilisé'),
        ('expired', 'Expiré'),
        ('cancelled', 'Annulé'),
    ]
    
    voucher_id = models.CharField(max_length=20, unique=True, editable=False, null=True, blank=True)
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='vouchers')
    issuing_doctor = models.ForeignKey('accounts.UserProfile', on_delete=models.CASCADE, related_name='issued_vouchers')
    issuing_facility = models.ForeignKey('facilities.Facility', on_delete=models.CASCADE, related_name='issued_vouchers')
    target_facility = models.ForeignKey('facilities.Facility', on_delete=models.CASCADE, related_name='received_vouchers')
    service_type = models.CharField(max_length=100, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    issue_date = models.DateField(default=timezone.now)
    expiry_date = models.DateField(default=get_default_expiry)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='issued')
    validated_by = models.ForeignKey('accounts.UserProfile', on_delete=models.SET_NULL, null=True, blank=True, related_name='validated_vouchers')
    validated_date = models.DateTimeField(null=True, blank=True)
    qr_code = models.ImageField(upload_to='vouchers/qr_codes/', blank=True, null=True)
    
    class Meta:
        verbose_name = "Bon de prise en charge"
        verbose_name_plural = "Bons de prise en charge"
        ordering = ['-issue_date']
    
    def save(self, *args, **kwargs):
        if not self.voucher_id:
            # Generate a unique voucher ID
            self.voucher_id = f"V-{uuid.uuid4().hex[:8].upper()}"
            
        # Generate QR code if it doesn't exist
        if not self.qr_code and self.voucher_id:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(self.voucher_id)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            self.qr_code.save(f"{self.voucher_id}.png", File(buffer), save=False)
            
        super().save(*args, **kwargs)
    
    def __str__(self):
        voucher_id = self.voucher_id or "Unassigned"
        return f"Bon {voucher_id} pour {self.patient}"
