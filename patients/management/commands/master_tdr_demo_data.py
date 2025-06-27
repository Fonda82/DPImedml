import datetime
import random
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import transaction
from accounts.models import UserProfile
from patients.models import Patient, MedicalRecord, ICD10Code, VitalSigns, Hospitalization, HospitalizationProgressNote, DischargeReport
from appointments.models import Appointment
from facilities.models import Facility, FacilityCapability, InterFacilityCommunication, FacilityNetwork
from rehabilitation.models import RehabilitationPlan, RehabilitationSession
from vouchers.models import Voucher
from prescriptions.models import Prescription, Medication, MedicationCategory, PrescriptionMedication
from referrals.models import Referral, ReferralResponse, ReferralFollowUp
from dashboard.models import SystemActivity, SecurityAudit, LoginAttempt, DataRetentionPolicy


class Command(BaseCommand):
    help = 'Master TDR Mali pediatric rehabilitation demo data with dashboard integration'
    
    def add_arguments(self, parser):
        parser.add_argument('--clean', action='store_true', help='Clean existing data before seeding')
        parser.add_argument('--skip-base', action='store_true', help='Skip base data (facilities, users, patients)')
    
    def handle(self, *args, **options):
        if options['clean']:
            self.clean_tdr_data()
        
        self.stdout.write(self.style.SUCCESS('🇲🇱 Creating Master TDR Demo Data for Dashboards...'))
        
        try:
            # Get existing data or create minimal set
            facilities = list(Facility.objects.all())
            doctors = list(UserProfile.objects.filter(user_type='doctor'))
            patients = list(Patient.objects.all())
            
            if not options['skip_base']:
                # Ensure we have minimum data
                if len(facilities) < 3:
                    facilities = self.create_basic_facilities()
                if len(doctors) < 5:
                    doctors = self.create_basic_doctors(facilities)
                if len(patients) < 10:
                    patients = self.create_basic_patients()
            
            if not facilities or not doctors or not patients:
                self.stdout.write(self.style.ERROR('❌ No base data found. Run without --skip-base first.'))
                return
            
            # Create TDR features for dashboard integration
            self.stdout.write('🏥 Creating TDR Hospitalization Data...')
            hospitalizations = self.create_hospitalizations(patients, doctors, facilities)
            self.create_hospitalization_progress(hospitalizations, doctors)
            
            self.stdout.write('🔄 Creating TDR Referral System...')
            referrals = self.create_referrals(patients, doctors, facilities)
            self.create_referral_responses(referrals, doctors)
            
            self.stdout.write('💬 Creating Inter-facility Communications...')
            self.create_inter_facility_communications(facilities, doctors)
            
            self.stdout.write('🔒 Creating Dashboard Security Data...')
            self.create_dashboard_security_data()
            
            self.stdout.write('📊 TDR Dashboard Statistics Summary:')
            self.display_dashboard_stats()
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error creating TDR demo data: {str(e)}'))
            raise e
        
        self.stdout.write(self.style.SUCCESS('🎉 Master TDR Demo Data created successfully!'))
        self.stdout.write('✅ All TDR features integrated with dashboard statistics')
    
    def clean_tdr_data(self):
        """Clean only TDR-specific data"""
        self.stdout.write('🧹 Cleaning TDR data...')
        
        # Delete TDR features only
        DischargeReport.objects.all().delete()
        HospitalizationProgressNote.objects.all().delete()
        Hospitalization.objects.all().delete()
        ReferralFollowUp.objects.all().delete()
        ReferralResponse.objects.all().delete()
        Referral.objects.all().delete()
        InterFacilityCommunication.objects.all().delete()
        SystemActivity.objects.all().delete()
        
        self.stdout.write('✅ TDR data cleaned')
    
    def create_basic_facilities(self):
        """Create minimum facilities for TDR demo"""
        facilities_data = [
            {
                'name': 'CSREF Commune I',
                'facility_type': 'CSRef',
                'address': 'Avenue de l\'Indépendance, Commune I',
                'city': 'Bamako',
                'region': 'District de Bamako - Commune I',
                'phone': '+223 20212223',
                'email': 'csref1@sante.ml',
            },
            {
                'name': 'Centre de Réadaptation Pédiatrique',
                'facility_type': 'CR',
                'address': 'Avenue du Mali, Badalabougou',
                'city': 'Bamako',
                'region': 'District de Bamako - Commune II',
                'phone': '+223 20232425',
                'email': 'crp@humanite-inclusion.org',
            },
            {
                'name': 'Hôpital Gabriel Touré - Pédiatrie',
                'facility_type': 'H',
                'address': 'Avenue de la Liberté',
                'city': 'Bamako',
                'region': 'District de Bamako - Commune VI',
                'phone': '+223 20293031',
                'email': 'pediatrie@hgt.sante.ml',
            }
        ]
        
        facilities = []
        for f_data in facilities_data:
            facility, created = Facility.objects.get_or_create(
                name=f_data['name'],
                defaults=f_data
            )
            facilities.append(facility)
        
        return facilities
    
    def create_basic_doctors(self, facilities):
        """Create minimum doctors for TDR demo"""
        doctor_data = [
            {'first_name': 'Dr. Adama', 'last_name': 'Traoré', 'specialty': 'Pédiatrie'},
            {'first_name': 'Dr. Fatoumata', 'last_name': 'Diallo', 'specialty': 'Neurologie'},
            {'first_name': 'Dr. Ibrahim', 'last_name': 'Koné', 'specialty': 'Réadaptation'},
            {'first_name': 'Dr. Mariam', 'last_name': 'Keita', 'specialty': 'Physiothérapie'},
            {'first_name': 'Dr. Oumar', 'last_name': 'Dembélé', 'specialty': 'Orthopédie'},
        ]
        
        doctors = []
        for i, doc_data in enumerate(doctor_data):
            username = f"dr.{doc_data['first_name'].lower().replace('dr. ', '')}.{doc_data['last_name'].lower()}"
            
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': doc_data['first_name'],
                    'last_name': doc_data['last_name'],
                    'email': f"{username}@sante.ml"
                }
            )
            
            if created:
                user.set_password('demo1234')
                user.save()
                
                user_profile = user.profile
                user_profile.user_type = 'doctor'
                user_profile.phone_number = f'+223{random.randint(60000000, 79999999)}'
                user_profile.facility = facilities[i % len(facilities)]
                user_profile.save()
            
            doctors.append(user.profile)
        
        return doctors
    
    def create_basic_patients(self):
        """Create minimum patients for TDR demo"""
        patient_names = [
            {'first': 'Ibrahim', 'last': 'Traoré'},
            {'first': 'Fatoumata', 'last': 'Diallo'},
            {'first': 'Mamadou', 'last': 'Koné'},
            {'first': 'Aïssata', 'last': 'Keita'},
            {'first': 'Oumar', 'last': 'Dembélé'},
            {'first': 'Aminata', 'last': 'Touré'},
            {'first': 'Adama', 'last': 'Coulibaly'},
            {'first': 'Fanta', 'last': 'Sangaré'},
            {'first': 'Seydou', 'last': 'Ballo'},
            {'first': 'Mariam', 'last': 'Cissé'},
        ]
        
        patients = []
        for i, name_data in enumerate(patient_names):
            age = random.randint(0, 14)
            today = datetime.date.today()
            date_of_birth = today - datetime.timedelta(days=age*365 + random.randint(0, 364))
            
            username = f"patient.{name_data['first'].lower()}.{name_data['last'].lower()}"
            
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': name_data['first'],
                    'last_name': name_data['last'],
                    'email': f"{username}@example.com"
                }
            )
            
            if created:
                user.set_password('demo1234')
                user.save()
                
                user_profile = user.profile
                user_profile.user_type = 'patient'
                user_profile.save()
            
            import hashlib
            patient_id = f"P-{hashlib.md5(f'{name_data["first"]}{name_data["last"]}{date_of_birth}'.encode()).hexdigest()[:8].upper()}"
            
            patient, created = Patient.objects.get_or_create(
                user=user,
                defaults={
                    'first_name': name_data['first'],
                    'last_name': name_data['last'],
                    'date_of_birth': date_of_birth,
                    'gender': random.choice(['M', 'F']),
                    'address': f"Bamako, Commune {random.randint(1, 6)}",
                    'phone_number': f'+223{random.randint(60000000, 79999999)}',
                    'guardian_name': f"{random.choice(['Adama', 'Fatoumata'])} {name_data['last']}",
                    'guardian_phone': f'+223{random.randint(60000000, 79999999)}',
                    'patient_id': patient_id,
                    'city': 'Bamako',
                    'region': f'District de Bamako - Commune {random.randint(1, 6)}'
                }
            )
            
            patients.append(patient)
        
        return patients
    
    def create_hospitalizations(self, patients, doctors, facilities):
        """Create hospitalizations for TDR compliance"""
        hospitalizations = []
        
        service_types = [
            'Pédiatrie A', 'Pédiatrie B', 'Réadaptation pédiatrique', 
            'Neurologie pédiatrique', 'Chirurgie pédiatrique', 'Soins intensifs pédiatriques'
        ]
        
        room_types = [
            'Chambre individuelle', 'Chambre double', 'Salle commune', 
            'Unité de soins intensifs', 'Salle de réadaptation'
        ]
        
        # Create hospitalizations for 40% of patients
        for patient in random.sample(patients, k=max(1, int(len(patients) * 0.4))):
            doctor = random.choice(doctors)
            facility = doctor.facility or random.choice(facilities)
            
            admission_date = timezone.now().date() - datetime.timedelta(days=random.randint(1, 180))
            
            # 60% discharged, 40% still admitted
            if random.random() < 0.6:
                discharge_date = admission_date + datetime.timedelta(days=random.randint(3, 21))
                status = 'discharged'
            else:
                discharge_date = None
                status = 'admitted'
            
            hospitalization = Hospitalization.objects.create(
                patient=patient,
                admitting_doctor=doctor,
                attending_doctor=doctor,
                admission_date=admission_date,
                discharge_date=discharge_date,
                admission_reason=f"Hospitalisation pour réadaptation pédiatrique",
                admission_diagnosis=f"Prise en charge spécialisée - {patient.first_name}",
                service_type=random.choice(service_types),
                room_number=f"{random.choice(['A', 'B', 'C'])}{random.randint(101, 350)}",
                room_type=random.choice(room_types),
                status=status
            )
            hospitalizations.append(hospitalization)
        
        self.stdout.write(f'🏥 Created {len(hospitalizations)} hospitalizations')
        return hospitalizations
    
    def create_hospitalization_progress(self, hospitalizations, doctors):
        """Create hospitalization progress notes"""
        progress_notes = 0
        
        for hospitalization in hospitalizations:
            # Create 2-4 progress notes per hospitalization
            num_notes = random.randint(2, 4)
            
            start_date = hospitalization.admission_date
            end_date = hospitalization.discharge_date or timezone.now().date()
            
            for i in range(num_notes):
                days_between = (end_date - start_date).days
                if days_between > 0:
                    note_date = start_date + datetime.timedelta(
                        days=i * (days_between // num_notes) if num_notes > 1 else 1
                    )
                else:
                    note_date = start_date
                
                HospitalizationProgressNote.objects.create(
                    hospitalization=hospitalization,
                    date=note_date,
                    doctor=random.choice(doctors),
                    clinical_notes=f"Évolution favorable du patient {hospitalization.patient.first_name}. Progression dans le programme de réadaptation.",
                    vital_signs_notes=f"Signes vitaux stables. Température: {random.uniform(36.5, 37.2):.1f}°C, FC: {random.randint(80, 120)}/min",
                    treatment_notes="Traitement de réadaptation adapté selon l'évolution clinique. Kinésithérapie quotidienne.",
                    plan_notes="Plan de soins maintenu avec surveillance renforcée. Évaluation progrès moteur."
                )
                progress_notes += 1
        
        self.stdout.write(f'📝 Created {progress_notes} progress notes')
    
    def create_referrals(self, patients, doctors, facilities):
        """Create inter-facility referrals"""
        referrals = []
        
        referral_types = [
            'consultation', 'rehabilitation', 'surgery', 'diagnostic', 'follow_up'
        ]
        
        urgency_levels = ['normal', 'high', 'urgent']
        
        # Create referrals for 30% of patients
        for patient in random.sample(patients, k=max(1, int(len(patients) * 0.3))):
            referring_doctor = random.choice(doctors)
            referring_facility = referring_doctor.facility or random.choice(facilities)
            
            # Choose different facility for referral
            receiving_facility = random.choice([f for f in facilities if f != referring_facility])
            
            referral_date = timezone.now().date() - datetime.timedelta(days=random.randint(1, 90))
            
            referral = Referral.objects.create(
                patient=patient,
                referring_facility=referring_facility,
                receiving_facility=receiving_facility,
                referring_doctor=referring_doctor,
                referral_type=random.choice(referral_types),
                referral_reason=f"Référence pour soins spécialisés en réadaptation pédiatrique",
                medical_summary=f"Patient {patient.first_name} nécessitant une prise en charge spécialisée en neurologie pédiatrique/réadaptation fonctionnelle. Évaluation développement psychomoteur recommandée.",
                urgency_level=random.choice(urgency_levels),
                preferred_date=referral_date + datetime.timedelta(days=random.randint(1, 30)),
                status=random.choice(['pending', 'accepted', 'completed', 'pending', 'accepted']),  # Weight toward accepted
                referral_date=referral_date
            )
            referrals.append(referral)
        
        self.stdout.write(f'🔄 Created {len(referrals)} inter-facility referrals')
        return referrals
    
    def create_referral_responses(self, referrals, doctors):
        """Create referral responses"""
        responses = 0
        
        for referral in referrals:
            if referral.status in ['accepted', 'completed']:
                # Find doctor at receiving facility
                receiving_doctors = [d for d in doctors if d.facility == referral.receiving_facility]
                if receiving_doctors:
                    receiving_doctor = random.choice(receiving_doctors)
                    
                    ReferralResponse.objects.create(
                        referral=referral,
                        responding_doctor=receiving_doctor,
                        response_date=referral.referral_date + datetime.timedelta(days=random.randint(1, 7)),
                        response_status='accepted' if referral.status == 'accepted' else 'completed',
                        response_notes=f"Référence acceptée pour {referral.patient.first_name}. RDV programmé pour évaluation spécialisée en réadaptation pédiatrique.",
                        proposed_appointment_date=referral.preferred_date + datetime.timedelta(days=random.randint(1, 14))
                    )
                    responses += 1
        
        self.stdout.write(f'📨 Created {responses} referral responses')
    
    def create_inter_facility_communications(self, facilities, doctors):
        """Create inter-facility communications"""
        communications = []
        
        communication_types = [
            'patient_referral', 'resource_sharing', 'information_request', 
            'coordination', 'emergency_notification', 'administrative'
        ]
        
        message_templates = {
            'patient_referral': "Référence patient {} pour soins spécialisés en réadaptation pédiatrique",
            'resource_sharing': "Demande de partage d'équipement de kinésithérapie pédiatrique",
            'information_request': "Demande d'information sur protocole de réadaptation pour paralysie cérébrale",
            'coordination': "Coordination pour prise en charge multidisciplinaire enfant 0-14 ans",
            'emergency_notification': "Notification urgente - patient pédiatrique critique nécessitant transfert",
            'administrative': "Communication administrative inter-établissements - réseau Mali"
        }
        
        patient_names = ['Ibrahim', 'Fatoumata', 'Mamadou', 'Aïssata', 'Oumar', 'Aminata']
        
        # Create 40+ communications between facilities
        for _ in range(random.randint(40, 65)):
            sending_facility = random.choice(facilities)
            receiving_facility = random.choice([f for f in facilities if f != sending_facility])
            
            sending_doctors = [d for d in doctors if d.facility == sending_facility]
            sender = random.choice(sending_doctors) if sending_doctors else random.choice(doctors)
            
            comm_type = random.choice(communication_types)
            
            communication = InterFacilityCommunication.objects.create(
                sending_facility=sending_facility,
                receiving_facility=receiving_facility,
                sender=sender,
                communication_type=comm_type,
                subject=f"Communication {comm_type.replace('_', ' ').title()} - Mali Réseau Pédiatrique",
                message=message_templates[comm_type].format(random.choice(patient_names)),
                urgency_level=random.choice(['low', 'normal', 'high']),
                status=random.choice(['sent', 'delivered', 'read', 'responded']),
                sent_date=timezone.now() - datetime.timedelta(days=random.randint(1, 90))
            )
            communications.append(communication)
        
        self.stdout.write(f'💬 Created {len(communications)} inter-facility communications')
    
    def create_dashboard_security_data(self):
        """Create security and audit data for dashboards"""
        try:
            # Create system activities for dashboard metrics
            activities = [
                'user_login', 'patient_created', 'appointment_scheduled', 
                'prescription_created', 'referral_sent', 'communication_sent',
                'hospitalization_created', 'medical_record_created'
            ]
            
            # Create 150 recent activities for dashboard statistics
            for _ in range(150):
                SystemActivity.objects.create(
                    user=User.objects.order_by('?').first(),
                    activity_type=random.choice(activities),
                    description=f"Activité système: {random.choice(activities).replace('_', ' ').title()}",
                    ip_address=f"192.168.1.{random.randint(1, 254)}",
                    timestamp=timezone.now() - datetime.timedelta(days=random.randint(1, 30))
                )
            
            self.stdout.write('🔒 Created dashboard security data')
        except Exception as e:
            self.stdout.write(f'⚠️ Skipped security data: {str(e)}')
    
    def display_dashboard_stats(self):
        """Display TDR statistics for dashboard verification"""
        try:
            total_hospitalizations = Hospitalization.objects.count()
            current_hospitalizations = Hospitalization.objects.filter(status='admitted').count()
            total_referrals = Referral.objects.count()
            pending_referrals = Referral.objects.filter(status='pending').count()
            accepted_referrals = Referral.objects.filter(status='accepted').count()
            total_communications = InterFacilityCommunication.objects.count()
            recent_communications = InterFacilityCommunication.objects.filter(
                sent_date__gte=timezone.now().date() - datetime.timedelta(days=7)
            ).count()
            
            self.stdout.write('📊 TDR Dashboard Statistics:')
            self.stdout.write(f'  🏥 Hospitalizations: {total_hospitalizations} total, {current_hospitalizations} current')
            self.stdout.write(f'  🔄 Referrals: {total_referrals} total, {pending_referrals} pending, {accepted_referrals} accepted')
            self.stdout.write(f'  💬 Communications: {total_communications} total, {recent_communications} this week')
            
        except Exception as e:
            self.stdout.write(f'⚠️ Could not display stats: {str(e)}') 