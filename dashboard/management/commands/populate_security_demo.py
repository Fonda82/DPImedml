from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import datetime, timedelta
import random

from dashboard.models import SecurityAudit, LoginAttempt, PatientConsent, DataRetentionPolicy
from patients.models import Patient


class Command(BaseCommand):
    help = 'Populate security and GDPR compliance demo data for tender presentation'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting security demo data population...'))
        
        # Create data retention policies
        self.create_retention_policies()
        
        # Create demo login attempts
        self.create_login_attempts()
        
        # Create security audit events
        self.create_security_audits()
        
        # Create patient consents
        self.create_patient_consents()
        
        self.stdout.write(self.style.SUCCESS('✅ Security and GDPR demo data populated successfully!'))
        self.stdout.write(self.style.WARNING('🔒 System ready for cybersecurity compliance demonstration'))

    def create_retention_policies(self):
        """Create realistic data retention policies for Mali healthcare"""
        policies = [
            {
                'data_type': 'medical_records',
                'retention_period_days': 2555,  # 7 years
                'description': 'Dossiers médicaux conservés 7 ans selon la réglementation malienne'
            },
            {
                'data_type': 'appointment_history',
                'retention_period_days': 1095,  # 3 years
                'description': 'Historique des rendez-vous conservé 3 ans pour suivi médical'
            },
            {
                'data_type': 'voucher_data',
                'retention_period_days': 1825,  # 5 years
                'description': 'Données des bons de prise en charge pour audit financier'
            },
            {
                'data_type': 'rehabilitation_plans',
                'retention_period_days': 2555,  # 7 years
                'description': 'Plans de réadaptation conservés pour continuité des soins'
            },
            {
                'data_type': 'system_logs',
                'retention_period_days': 365,   # 1 year
                'description': 'Journaux système pour sécurité et maintenance'
            }
        ]
        
        for policy_data in policies:
            policy, created = DataRetentionPolicy.objects.get_or_create(
                data_type=policy_data['data_type'],
                defaults={
                    'retention_period_days': policy_data['retention_period_days'],
                    'description': policy_data['description']
                }
            )
            if created:
                self.stdout.write(f'  ✓ Politique créée: {policy.get_data_type_display()}')

    def create_login_attempts(self):
        """Create realistic login attempt history"""
        # Get some users for realistic login attempts
        users = list(User.objects.all()[:10])
        
        # Generate login attempts for the last 7 days
        for day in range(7):
            date = timezone.now() - timedelta(days=day)
            
            # Generate 20-40 successful logins per day
            successful_logins = random.randint(20, 40)
            for _ in range(successful_logins):
                user = random.choice(users)
                LoginAttempt.objects.create(
                    username=user.username,
                    ip_address=self.generate_mali_ip(),
                    success=True,
                    timestamp=date - timedelta(hours=random.randint(0, 23), 
                                               minutes=random.randint(0, 59)),
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                )
            
            # Generate 0-3 failed logins per day (low failure rate = good security)
            failed_logins = random.randint(0, 3)
            for _ in range(failed_logins):
                LoginAttempt.objects.create(
                    username=random.choice(['admin', 'test', 'administrator', 'root']),
                    ip_address=self.generate_suspicious_ip(),
                    success=False,
                    timestamp=date - timedelta(hours=random.randint(0, 23),
                                               minutes=random.randint(0, 59)),
                    failure_reason='Invalid credentials',
                    user_agent='curl/7.68.0'
                )
        
        self.stdout.write(f'  ✓ Tentatives de connexion créées (taux de réussite: ~95%)')

    def create_security_audits(self):
        """Create realistic security audit events"""
        users = list(User.objects.all()[:5])
        
        # High-impact security events
        events = [
            {
                'audit_type': 'login_success',
                'description': 'Connexion réussie depuis nouvel appareil Mali',
                'risk_level': 'low',
                'hours_ago': random.randint(1, 24)
            },
            {
                'audit_type': 'gdpr_request',
                'description': 'Export de données patient pour conformité RGPD',
                'risk_level': 'medium',
                'hours_ago': random.randint(2, 48)
            },
            {
                'audit_type': 'data_access',
                'description': 'Accès aux dossiers médicaux depuis Bamako',
                'risk_level': 'low',
                'hours_ago': random.randint(1, 12)
            },
            {
                'audit_type': 'login_failed',
                'description': 'Tentative de connexion échouée - IP suspecte bloquée',
                'risk_level': 'medium',
                'hours_ago': random.randint(6, 72)
            },
            {
                'audit_type': 'permission_change',
                'description': 'Modification des permissions utilisateur par admin',
                'risk_level': 'high',
                'hours_ago': random.randint(24, 168)
            },
            {
                'audit_type': 'data_access',
                'description': 'Consultation sécurisée des données patient par médecin',
                'risk_level': 'low',
                'hours_ago': random.randint(1, 6)
            }
        ]
        
        for event_data in events:
            user = random.choice(users) if event_data['audit_type'] != 'login_failed' else None
            
            SecurityAudit.objects.create(
                user=user,
                audit_type=event_data['audit_type'],
                description=event_data['description'],
                timestamp=timezone.now() - timedelta(hours=event_data['hours_ago']),
                ip_address=self.generate_mali_ip() if user else self.generate_suspicious_ip(),
                risk_level=event_data['risk_level']
            )
        
        self.stdout.write(f'  ✓ Événements d\'audit de sécurité créés')

    def create_patient_consents(self):
        """Create GDPR consent records for patients"""
        patients = list(Patient.objects.all())
        users = list(User.objects.filter(profile__user_type__in=['doctor', 'facility_admin']))
        
        if not patients or not users:
            self.stdout.write(self.style.WARNING('  ⚠ Pas de patients ou d\'utilisateurs trouvés'))
            return
        
        # Create consents for most patients (high compliance rate)
        consent_types = PatientConsent.CONSENT_TYPES
        
        for patient in patients[:int(len(patients) * 0.85)]:  # 85% have consents
            granted_by = random.choice(users)
            
            # Each patient has 2-4 types of consent
            num_consents = random.randint(2, 4)
            selected_consents = random.sample(consent_types, num_consents)
            
            for consent_type, _ in selected_consents:
                # 95% of consents are granted (excellent compliance)
                granted = random.random() < 0.95
                
                consent_date = timezone.now() - timedelta(
                    days=random.randint(1, 365),
                    hours=random.randint(0, 23)
                )
                
                legal_basis = self.get_legal_basis(consent_type)
                
                PatientConsent.objects.create(
                    patient=patient,
                    consent_type=consent_type,
                    granted=granted,
                    granted_at=consent_date,
                    granted_by=granted_by,
                    legal_basis=legal_basis
                )
        
        # Calculate and display compliance rate
        total_patients = Patient.objects.count()
        patients_with_consent = Patient.objects.filter(consents__granted=True).distinct().count()
        compliance_rate = (patients_with_consent / total_patients * 100) if total_patients > 0 else 0
        
        self.stdout.write(f'  ✓ Consentements RGPD créés - Taux de conformité: {compliance_rate:.1f}%')

    def generate_mali_ip(self):
        """Generate realistic IP addresses from Mali"""
        # Mali ISP IP ranges (simplified)
        mali_ranges = [
            '196.200.',
            '41.223.',
            '154.118.',
            '197.231.'
        ]
        base = random.choice(mali_ranges)
        return f"{base}{random.randint(1, 254)}.{random.randint(1, 254)}"

    def generate_suspicious_ip(self):
        """Generate suspicious IP addresses for failed login attempts"""
        suspicious_patterns = [
            ('185.220.', 2),  # TOR exit nodes - needs 2 more octets
            ('91.134.', 2),   # VPN ranges - needs 2 more octets  
            ('45.61.', 2),    # Suspicious range - needs 2 more octets
            ('192.168.', 2)   # Internal network (misconfig) - needs 2 more octets
        ]
        base, octets_needed = random.choice(suspicious_patterns)
        if octets_needed == 2:
            return f"{base}{random.randint(1, 254)}.{random.randint(1, 254)}"
        else:
            return f"{base}{random.randint(1, 254)}"

    def get_legal_basis(self, consent_type):
        """Get appropriate legal basis for each consent type under GDPR"""
        legal_bases = {
            'data_processing': 'Article 6(1)(a) RGPD - Consentement explicite pour traitement des données de santé',
            'medical_records': 'Article 9(2)(h) RGPD - Médecine préventive, diagnostic médical, prise en charge sanitaire',
            'sharing_partners': 'Article 6(1)(a) RGPD - Consentement pour partage avec partenaires de soins',
            'marketing': 'Article 6(1)(a) RGPD - Consentement pour communications marketing',
            'research': 'Article 9(2)(j) RGPD - Recherche scientifique avec garanties appropriées'
        }
        return legal_bases.get(consent_type, 'Article 6(1)(a) RGPD - Consentement explicite')

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Clear existing security data before populating',
        ) 