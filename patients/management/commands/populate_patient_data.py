from django.core.management.base import BaseCommand
from django.utils import timezone
from patients.models import Patient
from rehabilitation.models import RehabilitationPlan, RehabilitationSession
from vouchers.models import Voucher
from accounts.models import UserProfile
from facilities.models import Facility
from datetime import timedelta
import random

class Command(BaseCommand):
    help = 'Add rehabilitation plans and vouchers to patients who don\'t have them'

    def handle(self, *args, **options):
        self.stdout.write('🎯 Adding rehabilitation plans and vouchers to patients...')
        
        # Get patients without rehabilitation plans
        patients_without_rehab = Patient.objects.filter(
            rehabilitation_plans__isnull=True
        ).distinct()
        
        # Get patients without vouchers  
        patients_without_vouchers = Patient.objects.filter(
            vouchers__isnull=True
        ).distinct()
        
        # Get doctors and facilities
        doctors = list(UserProfile.objects.filter(user_type='doctor'))
        facilities = list(Facility.objects.all())
        
        if not doctors or not facilities:
            self.stdout.write('❌ No doctors or facilities found')
            return
        
        # Add rehabilitation plans to patients without them
        rehab_diagnoses = [
            'Plan de kinésithérapie motrice',
            'Rééducation post-traumatique', 
            'Thérapie occupationnelle',
            'Rééducation neurologique',
            'Plan de réadaptation fonctionnelle'
        ]
        
        rehab_goals = [
            'Améliorer la mobilité articulaire\nRenforcer les muscles\nDévelopper l\'autonomie',
            'Réduire la douleur\nRestorer la fonction motrice\nPrévenir les complications',
            'Développer les compétences quotidiennes\nAméliorer la coordination\nRenforcer l\'indépendance',
            'Stimuler la neuroplasticité\nAméliorer l\'équilibre\nRenforcer la marche',
            'Optimiser les capacités fonctionnelles\nFavoriser l\'inclusion sociale\nAméliorer la qualité de vie'
        ]
        
        added_rehab = 0
        for patient in patients_without_rehab[:30]:  # Add to 30 patients
            diagnosis = random.choice(rehab_diagnoses)
            goals = random.choice(rehab_goals)
            
            # Create rehabilitation plan
            rehab_plan = RehabilitationPlan.objects.create(
                patient=patient,
                prescribing_doctor=random.choice(doctors),
                start_date=timezone.now().date() - timedelta(days=random.randint(1, 30)),
                diagnosis=diagnosis,
                goals=goals,
                status='active'
            )
            
            # Create 2-3 sessions for each plan
            for i in range(random.randint(2, 3)):
                session_date = rehab_plan.start_date + timedelta(days=i*7)
                RehabilitationSession.objects.create(
                    rehabilitation_plan=rehab_plan,
                    session_date=session_date,
                    duration_minutes=random.randint(30, 60),
                    notes=f'Session {i+1}: Patient montre des progrès {random.choice(["satisfaisants", "encourageants", "constants"])}',
                    status='completed' if session_date <= timezone.now().date() else 'planned'
                )
            
            added_rehab += 1
        
        # Add vouchers to patients without them
        voucher_services = [
            'Consultation nutritionnelle',
            'Évaluation psychomotrice', 
            'Séance de kinésithérapie',
            'Consultation pédiatrique',
            'Bilan orthophonique',
            'Consultation ergothérapie'
        ]
        
        added_vouchers = 0
        for patient in patients_without_vouchers[:50]:  # Add to 50 patients
            # Create 2-4 vouchers per patient
            for _ in range(random.randint(2, 4)):
                service = random.choice(voucher_services)
                
                Voucher.objects.create(
                    patient=patient,
                    issuing_facility=random.choice(facilities),
                    target_facility=random.choice(facilities),
                    service_type=service,
                    status=random.choice(['issued', 'validated', 'used']),
                    issue_date=timezone.now().date() - timedelta(days=random.randint(1, 60)),
                    expiry_date=(timezone.now() + timedelta(days=30)).date(),
                    issuing_doctor=random.choice(doctors)
                )
            
            added_vouchers += 1
        
        self.stdout.write(f'✅ Added rehabilitation plans to {added_rehab} patients')
        self.stdout.write(f'✅ Added vouchers to {added_vouchers} patients')
        
        # Final statistics
        total_with_rehab = Patient.objects.filter(rehabilitation_plans__isnull=False).distinct().count()
        total_with_vouchers = Patient.objects.filter(vouchers__isnull=False).distinct().count()
        total_patients = Patient.objects.count()
        
        self.stdout.write(f'\n📊 Final statistics:')
        self.stdout.write(f'   Patients with rehabilitation plans: {total_with_rehab}/{total_patients} ({int(total_with_rehab/total_patients*100)}%)')
        self.stdout.write(f'   Patients with vouchers: {total_with_vouchers}/{total_patients} ({int(total_with_vouchers/total_patients*100)}%)')
        self.stdout.write('✅ Patient data population completed!') 