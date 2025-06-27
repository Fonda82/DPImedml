from django.db import models
from django.utils import timezone
import uuid

# Create your models here.

class Facility(models.Model):
    FACILITY_TYPES = [
        ('CSCom', 'Centre de Santé Communautaire'),
        ('CSRef', 'Centre de Santé de Référence'),
        ('CR', 'Centre de Réadaptation'),
        ('H', 'Hôpital'),
        ('P', 'Poste de Santé'),
        ('A', 'Autre'),
    ]
    
    name = models.CharField(max_length=200, verbose_name="Nom de la structure", null=True, blank=True)
    facility_type = models.CharField(max_length=10, choices=FACILITY_TYPES, verbose_name="Type de structure", null=True, blank=True)
    address = models.CharField(max_length=255, verbose_name="Adresse", null=True, blank=True)
    city = models.CharField(max_length=100, default="Bamako", verbose_name="Ville", null=True, blank=True)
    region = models.CharField(max_length=100, verbose_name="Région", null=True, blank=True)
    country = models.CharField(max_length=100, default="Mali", verbose_name="Pays", null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Téléphone")
    email = models.EmailField(blank=True, null=True, verbose_name="Email")
    year_established = models.PositiveIntegerField(blank=True, null=True, verbose_name="Année de création")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    
    # Enhanced Communication Features for TDR
    facility_code = models.CharField(max_length=20, unique=True, null=True, blank=True, verbose_name="Code établissement")
    coordinates_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name="Latitude")
    coordinates_lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name="Longitude")
    
    # Network and Communication
    network_member = models.BooleanField(default=True, verbose_name="Membre du réseau")
    accepts_referrals = models.BooleanField(default=True, verbose_name="Accepte les références")
    can_send_referrals = models.BooleanField(default=True, verbose_name="Peut envoyer des références")
    voucher_validation_enabled = models.BooleanField(default=True, verbose_name="Validation bons activée")
    
    # Operating Hours
    operating_hours = models.TextField(blank=True, verbose_name="Heures d'ouverture")
    emergency_contact = models.CharField(max_length=20, blank=True, verbose_name="Contact urgence")
    
    class Meta:
        verbose_name = "Structure sanitaire"
        verbose_name_plural = "Structures sanitaires"
        ordering = ['name']
    
    def __str__(self):
        name = self.name or "Unnamed facility"
        facility_type = self.get_facility_type_display() if self.facility_type else "Unknown type"
        return f"{name} ({facility_type})"
    
    def save(self, *args, **kwargs):
        if not self.facility_code:
            self.facility_code = self.generate_facility_code()
        super().save(*args, **kwargs)
    
    def generate_facility_code(self):
        """Generate unique facility code: FAC-XXXX"""
        import random
        import string
        
        while True:
            code = f"FAC-{''.join(random.choices(string.digits, k=4))}"
            if not Facility.objects.filter(facility_code=code).exists():
                return code


class FacilityCapability(models.Model):
    """
    Track specific capabilities/specialties of each facility
    """
    
    CAPABILITY_TYPES = [
        ('specialty', 'Spécialité médicale'),
        ('service', 'Service disponible'),
        ('equipment', 'Équipement'),
        ('program', 'Programme spécialisé'),
    ]
    
    SPECIALTY_CHOICES = [
        ('pediatrics', 'Pédiatrie'),
        ('rehabilitation', 'Réadaptation'),
        ('orthopedics', 'Orthopédie'),
        ('neurology', 'Neurologie'),
        ('psychology', 'Psychologie'),
        ('physiotherapy', 'Kinésithérapie'),
        ('occupational_therapy', 'Ergothérapie'),
        ('speech_therapy', 'Orthophonie'),
        ('surgery', 'Chirurgie'),
        ('radiology', 'Radiologie'),
        ('laboratory', 'Laboratoire'),
        ('nutrition', 'Nutrition'),
        ('social_work', 'Service social'),
    ]
    
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name='capabilities')
    capability_type = models.CharField(max_length=20, choices=CAPABILITY_TYPES)
    name = models.CharField(max_length=100, choices=SPECIALTY_CHOICES, verbose_name="Nom")
    description = models.TextField(blank=True, verbose_name="Description")
    is_available = models.BooleanField(default=True, verbose_name="Disponible")
    capacity_level = models.CharField(max_length=20, choices=[
        ('basic', 'Basique'),
        ('intermediate', 'Intermédiaire'),
        ('advanced', 'Avancé'),
        ('expert', 'Expert'),
    ], default='basic', verbose_name="Niveau")
    
    # Availability
    available_days = models.CharField(max_length=50, blank=True, verbose_name="Jours disponibles")
    available_hours = models.CharField(max_length=50, blank=True, verbose_name="Heures disponibles")
    
    # Capacity
    max_patients_per_day = models.PositiveIntegerField(null=True, blank=True, verbose_name="Patients max/jour")
    current_wait_time_days = models.PositiveIntegerField(null=True, blank=True, verbose_name="Délai d'attente (jours)")
    
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Capacité établissement"
        verbose_name_plural = "Capacités établissements"
        unique_together = [['facility', 'name']]
    
    def __str__(self):
        return f"{self.facility.name} - {self.get_name_display()}"


class InterFacilityCommunication(models.Model):
    """
    Track communication between facilities
    """
    
    COMMUNICATION_TYPES = [
        ('referral', 'Référence patient'),
        ('voucher_validation', 'Validation bon'),
        ('information_request', 'Demande d\'information'),
        ('resource_sharing', 'Partage de ressources'),
        ('emergency_notification', 'Notification urgence'),
        ('administrative', 'Administratif'),
    ]
    
    STATUS_CHOICES = [
        ('sent', 'Envoyé'),
        ('delivered', 'Livré'),
        ('read', 'Lu'),
        ('responded', 'Répondu'),
        ('failed', 'Échec'),
    ]
    
    # Communication Details
    communication_id = models.UUIDField(default=uuid.uuid4, unique=True)
    from_facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name='sent_communications')
    to_facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name='received_communications')
    
    communication_type = models.CharField(max_length=25, choices=COMMUNICATION_TYPES)
    subject = models.CharField(max_length=200, verbose_name="Sujet")
    message = models.TextField(verbose_name="Message")
    
    # Related Objects
    related_patient = models.ForeignKey('patients.Patient', on_delete=models.SET_NULL, null=True, blank=True)
    related_referral = models.ForeignKey('referrals.Referral', on_delete=models.SET_NULL, null=True, blank=True)
    related_voucher = models.ForeignKey('vouchers.Voucher', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Status Tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='sent')
    sent_by = models.ForeignKey('accounts.UserProfile', on_delete=models.SET_NULL, null=True, related_name='sent_communications')
    received_by = models.ForeignKey('accounts.UserProfile', on_delete=models.SET_NULL, null=True, blank=True, related_name='received_communications')
    
    # Timestamps
    sent_date = models.DateTimeField(auto_now_add=True)
    delivered_date = models.DateTimeField(null=True, blank=True)
    read_date = models.DateTimeField(null=True, blank=True)
    response_date = models.DateTimeField(null=True, blank=True)
    
    # Response
    response_message = models.TextField(blank=True, verbose_name="Message de réponse")
    response_by = models.ForeignKey('accounts.UserProfile', on_delete=models.SET_NULL, null=True, blank=True, related_name='communication_responses')
    
    # Priority
    is_urgent = models.BooleanField(default=False, verbose_name="Urgent")
    requires_response = models.BooleanField(default=False, verbose_name="Réponse requise")
    
    class Meta:
        verbose_name = "Communication inter-établissements"
        verbose_name_plural = "Communications inter-établissements"
        ordering = ['-sent_date']
    
    def __str__(self):
        return f"{self.get_communication_type_display()}: {self.from_facility.name} → {self.to_facility.name}"
    
    @property
    def response_time_hours(self):
        """Calculate response time in hours"""
        if self.response_date and self.sent_date:
            return (self.response_date - self.sent_date).total_seconds() / 3600
        return None


class FacilityNetwork(models.Model):
    """
    Define networks of facilities that work together
    """
    
    NETWORK_TYPES = [
        ('regional', 'Réseau régional'),
        ('specialty', 'Réseau de spécialité'),
        ('referral', 'Réseau de référence'),
        ('emergency', 'Réseau d\'urgence'),
    ]
    
    name = models.CharField(max_length=200, verbose_name="Nom du réseau")
    network_type = models.CharField(max_length=20, choices=NETWORK_TYPES)
    description = models.TextField(blank=True, verbose_name="Description")
    
    # Network Members
    facilities = models.ManyToManyField(Facility, through='FacilityNetworkMembership', related_name='networks')
    
    # Network Coordinator
    coordinator_facility = models.ForeignKey(Facility, on_delete=models.SET_NULL, null=True, blank=True, related_name='coordinated_networks')
    coordinator_contact = models.ForeignKey('accounts.UserProfile', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    created_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Réseau d'établissements"
        verbose_name_plural = "Réseaux d'établissements"
    
    def __str__(self):
        return f"{self.name} ({self.get_network_type_display()})"


class FacilityNetworkMembership(models.Model):
    """
    Track facility membership in networks
    """
    
    ROLE_CHOICES = [
        ('member', 'Membre'),
        ('coordinator', 'Coordinateur'),
        ('referral_hub', 'Hub de référence'),
    ]
    
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE)
    network = models.ForeignKey(FacilityNetwork, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    
    joined_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    # Permissions within network
    can_send_referrals = models.BooleanField(default=True)
    can_receive_referrals = models.BooleanField(default=True)
    can_validate_vouchers = models.BooleanField(default=True)
    
    class Meta:
        unique_together = [['facility', 'network']]
        verbose_name = "Adhésion réseau"
        verbose_name_plural = "Adhésions réseaux"
    
    def __str__(self):
        return f"{self.facility.name} dans {self.network.name} ({self.get_role_display()})"


class VoucherValidationLog(models.Model):
    """
    Track voucher validations across facilities
    """
    
    VALIDATION_TYPES = [
        ('creation', 'Création'),
        ('validation', 'Validation'),
        ('redemption', 'Utilisation'),
        ('cancellation', 'Annulation'),
        ('transfer', 'Transfert'),
    ]
    
    STATUS_CHOICES = [
        ('success', 'Succès'),
        ('failed', 'Échec'),
        ('pending', 'En attente'),
    ]
    
    voucher = models.ForeignKey('vouchers.Voucher', on_delete=models.CASCADE, related_name='validation_logs')
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name='voucher_validations')
    validation_type = models.CharField(max_length=20, choices=VALIDATION_TYPES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    
    # Details
    validated_by = models.ForeignKey('accounts.UserProfile', on_delete=models.SET_NULL, null=True)
    validation_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, verbose_name="Notes")
    
    # Cross-facility validation
    originating_facility = models.ForeignKey(Facility, on_delete=models.SET_NULL, null=True, blank=True, related_name='voucher_origins')
    validation_response_time = models.PositiveIntegerField(null=True, blank=True, help_text="Temps de réponse en secondes")
    
    class Meta:
        verbose_name = "Log validation bon"
        verbose_name_plural = "Logs validation bons"
        ordering = ['-validation_date']
    
    def __str__(self):
        return f"{self.voucher.voucher_id} - {self.get_validation_type_display()} à {self.facility.name}"
