from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import UserProfile
from patients.models import Patient
from appointments.models import Appointment
from vouchers.models import Voucher
from rehabilitation.models import RehabilitationPlan, RehabilitationSession
from django.utils import timezone
from datetime import datetime, timedelta
import random

class Command(BaseCommand):
    help = 'Link demo users to existing patient data for proper dashboard functionality'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔗 Linking demo users to patient data...'))
        
        try:
            # Get or create the demo patient user
            patient_user, created = User.objects.get_or_create(
                username='patient',
                defaults={
                    'first_name': 'Ibrahim',
                    'last_name': 'Koné',
                    'email': 'ibrahim.kone@example.com',
                    'is_active': True
                }
            )
            
            if created:
                patient_user.set_password('patient123')
                patient_user.save()
                self.stdout.write(f"✅ Created patient user: {patient_user.username}")
            
            # Get or create patient profile
            patient_profile, created = UserProfile.objects.get_or_create(
                user=patient_user,
                defaults={
                    'user_type': 'patient',
                    'phone_number': '+223 76 12 34 56',
                    'address': 'Commune I, Bamako, Mali'
                }
            )
            
            if created:
                self.stdout.write(f"✅ Created patient profile for: {patient_user.username}")
            
            # Find a Mali demo patient to link to this user
            demo_patients = Patient.objects.filter(first_name='Ibrahim', last_name='Koné')
            
            if demo_patients.exists():
                demo_patient = demo_patients.first()
                # Link the user to this patient
                demo_patient.user = patient_user
                demo_patient.save()
                self.stdout.write(f"✅ Linked user to Patient: {demo_patient}")
                
                # Link appointments to this patient
                appointments = Appointment.objects.filter(patient=demo_patient)[:5]
                appointment_count = appointments.count()
                self.stdout.write(f"✅ Found {appointment_count} appointments for patient")
                
                # Create future appointments if none exist
                if appointment_count == 0:
                    doctors = UserProfile.objects.filter(user_type='doctor')[:3]
                    if doctors.exists():
                        for i in range(3):
                            future_date = timezone.now() + timedelta(days=random.randint(1, 30))
                            appointment = Appointment.objects.create(
                                patient=demo_patient,
                                doctor=doctors[i % len(doctors)],
                                facility=doctors[i % len(doctors)].facility,
                                appointment_date=future_date,
                                reason='Consultation de suivi',
                                status='scheduled',
                                notes='Rendez-vous de contrôle pour suivi du traitement'
                            )
                            self.stdout.write(f"✅ Created appointment: {appointment}")
                
                # Link vouchers to this patient
                vouchers = Voucher.objects.filter(patient=demo_patient)[:3]
                voucher_count = vouchers.count()
                self.stdout.write(f"✅ Found {voucher_count} vouchers for patient")
                
                # Create vouchers if none exist
                if voucher_count == 0:
                    from facilities.models import Facility
                    facilities = Facility.objects.all()[:2]
                    
                    if facilities.exists():
                        # Create active vouchers
                        for i, service_type in enumerate(['Consultation générale', 'Kinésithérapie', 'Orthophonie']):
                            voucher = Voucher.objects.create(
                                patient=demo_patient,
                                issuing_facility=facilities[i % len(facilities)],
                                target_facility=facilities[i % len(facilities)],
                                service_type=service_type,
                                status='issued',
                                issue_date=timezone.now().date(),
                                expiry_date=(timezone.now() + timedelta(days=30)).date(),
                                issuing_doctor=patient_profile
                            )
                            self.stdout.write(f"✅ Created voucher: {voucher}")
                
                # Link rehabilitation plans
                rehab_plans = RehabilitationPlan.objects.filter(patient=demo_patient)
                if not rehab_plans.exists():
                    # Create a rehabilitation plan
                    rehab_plan = RehabilitationPlan.objects.create(
                        patient=demo_patient,
                        doctor=UserProfile.objects.filter(user_type='doctor').first(),
                        facility=patient_profile.facility or UserProfile.objects.filter(user_type='doctor').first().facility,
                        title='Programme de réhabilitation pédiatrique',
                        description='Plan complet de réhabilitation pour paralysie cérébrale',
                        goals='Améliorer la mobilité, développer la communication, renforcer l\'autonomie',
                        start_date=timezone.now().date(),
                        estimated_duration=180,  # 6 months
                        status='active'
                    )
                    
                    # Create rehabilitation sessions
                    for i in range(8):
                        session_date = timezone.now().date() + timedelta(weeks=i)
                        status = 'completed' if i < 5 else 'scheduled'
                        
                        RehabilitationSession.objects.create(
                            rehabilitation_plan=rehab_plan,
                            session_date=session_date,
                            duration=60,
                            exercises_performed='Exercices de mobilité, étirements, activités cognitives',
                            progress_notes=f'Session {i+1}: Progrès notable en mobilité' if status == 'completed' else '',
                            next_session_plan='Continuer les exercices de renforcement',
                            status=status,
                            created_by=UserProfile.objects.filter(user_type='doctor').first()
                        )
                    
                    self.stdout.write(f"✅ Created rehabilitation plan with 8 sessions: {rehab_plan}")
                
                self.stdout.write(self.style.SUCCESS(f'🎯 Successfully linked demo patient user to Patient ID: {demo_patient.id}'))
                
            else:
                self.stdout.write(self.style.WARNING('⚠️  No Mali demo patients found. Run enhanced_mali_demo_data first.'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error linking demo users: {str(e)}'))
            
        self.stdout.write(self.style.SUCCESS('✅ Demo user linking completed!')) 