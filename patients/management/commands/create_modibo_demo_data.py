from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import UserProfile
from patients.models import Patient
from appointments.models import Appointment
from vouchers.models import Voucher
from rehabilitation.models import RehabilitationPlan, RehabilitationSession
from facilities.models import Facility
from django.utils import timezone
from datetime import timedelta, datetime
import random

class Command(BaseCommand):
    help = 'Create additional demo data for Modibo Kané patient'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🎯 Creating demo data for Modibo Kané...'))
        
        try:
            # Get the patient user and record
            patient_user = User.objects.get(username='patient')
            patient = Patient.objects.get(user=patient_user)
            
            self.stdout.write(f"📋 Working with patient: {patient.first_name} {patient.last_name} (ID: {patient.patient_id})")
            
            # Get some doctors and facilities
            doctors = UserProfile.objects.filter(user_type='doctor')[:5]
            facilities = Facility.objects.all()[:3]
            
            if not doctors.exists() or not facilities.exists():
                self.stdout.write(self.style.ERROR('❌ Need doctors and facilities in the system first'))
                return
            
            # 1. Create additional appointments
            self.stdout.write('\n📅 Creating appointments...')
            existing_appointments = Appointment.objects.filter(patient=patient).count()
            
            for i in range(4):  # Create 4 more appointments
                future_date = timezone.now() + timedelta(days=random.randint(1, 60))
                appointment_type = random.choice([
                    'Consultation de suivi',
                    'Séance de kinésithérapie',
                    'Consultation orthophonie',
                    'Évaluation nutritionnelle',
                    'Contrôle médical'
                ])
                
                appointment = Appointment.objects.create(
                    patient=patient,
                    doctor=random.choice(doctors),
                    facility=random.choice(facilities),
                    appointment_date=future_date,
                    reason=appointment_type,
                    status='scheduled',
                    notes=f'Rendez-vous programmé pour {appointment_type.lower()}'
                )
                self.stdout.write(f"✅ Created appointment: {appointment.reason} - {appointment.appointment_date.strftime('%d/%m/%Y')}")
            
            # 2. Create additional vouchers  
            self.stdout.write('\n🎫 Creating vouchers...')
            
            voucher_services = [
                'Consultation kinésithérapie',
                'Séance orthophonie', 
                'Consultation nutritionnelle',
                'Évaluation psychomotrice',
                'Consultation pédiatrique'
            ]
            
            for service in voucher_services:
                voucher = Voucher.objects.create(
                    patient=patient,
                    issuing_facility=random.choice(facilities),
                    target_facility=random.choice(facilities),
                    service_type=service,
                    status=random.choice(['issued', 'validated']),
                    issue_date=timezone.now().date(),
                    expiry_date=(timezone.now() + timedelta(days=30)).date(),
                    issuing_doctor=random.choice(doctors)
                )
                self.stdout.write(f"✅ Created voucher: {service}")
            
            # 3. Enhance rehabilitation plan with exercises
            self.stdout.write('\n🏃‍♂️ Creating exercise sessions...')
            
            # Get or create rehabilitation plan
            rehab_plan = RehabilitationPlan.objects.filter(patient=patient).first()
            if not rehab_plan:
                rehab_plan = RehabilitationPlan.objects.create(
                    patient=patient,
                    prescribing_doctor=random.choice(doctors),
                    start_date=timezone.now().date(),
                    diagnosis='Plan personnalisé pour améliorer la mobilité et l\'autonomie',
                    goals='Renforcer la mobilité, développer l\'autonomie, améliorer la communication',
                    status='active'
                )
                self.stdout.write(f"✅ Created rehabilitation plan")
            
            # Create exercise sessions with detailed notes
            exercise_sessions = [
                {
                    'type': 'physiotherapy',
                    'notes': 'Exercices de mobilité des membres inférieurs:\n- Étirements des jambes (3x15 répétitions)\n- Exercices d\'équilibre (2 minutes)\n- Renforcement musculaire doux\n- Marche assistée',
                    'duration': 45
                },
                {
                    'type': 'speech_therapy', 
                    'notes': 'Séance de stimulation du langage:\n- Exercices de prononciation (voyelles et consonnes)\n- Jeux de mots et répétition\n- Lecture guidée (10 minutes)\n- Exercices de souffle',
                    'duration': 30
                },
                {
                    'type': 'occupational_therapy',
                    'notes': 'Activités de coordination:\n- Exercices de préhension fine\n- Jeux de coordination œil-main\n- Activités de latéralisation\n- Parcours moteur adapté',
                    'duration': 40
                },
                {
                    'type': 'occupational_therapy',
                    'notes': 'Entraînement aux activités quotidiennes:\n- Exercices d\'habillage\n- Manipulation d\'objets du quotidien\n- Exercices d\'écriture adaptée\n- Autonomie alimentaire',
                    'duration': 35
                },
                {
                    'type': 'psychological_support',
                    'notes': 'Activités de stimulation mentale:\n- Jeux de mémoire visuelle\n- Exercices de logique simple\n- Activités de concentration\n- Puzzles adaptés à l\'âge',
                    'duration': 25
                }
            ]
            
            for i, session_data in enumerate(exercise_sessions):
                session_date = timezone.now() + timedelta(weeks=i)
                status = 'completed' if i < 3 else 'planned'
                
                session = RehabilitationSession.objects.create(
                    rehabilitation_plan=rehab_plan,
                    session_date=session_date,
                    duration_minutes=session_data['duration'],
                    session_type=session_data['type'],
                    notes=session_data['notes'],
                    next_session_recommendations='Continuer les exercices selon progression',
                    status=status,
                    therapist=random.choice(doctors)
                )
                self.stdout.write(f"✅ Created {session_data['type']} session ({status})")
            
            # Summary
            total_appointments = Appointment.objects.filter(patient=patient).count()
            total_vouchers = Voucher.objects.filter(patient=patient).count()
            total_sessions = RehabilitationSession.objects.filter(rehabilitation_plan__patient=patient).count()
            
            self.stdout.write(f'\n📊 Final counts for {patient.first_name} {patient.last_name}:')
            self.stdout.write(f"📅 Appointments: {total_appointments}")
            self.stdout.write(f"🎫 Vouchers: {total_vouchers}")
            self.stdout.write(f"🏃‍♂️ Exercise sessions: {total_sessions}")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error creating demo data: {str(e)}'))
            
        self.stdout.write(self.style.SUCCESS('✅ Demo data creation completed!')) 