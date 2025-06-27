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
    help = 'Master Mali pediatric rehabilitation demo data with full TDR compliance'
    
    def add_arguments(self, parser):
        parser.add_argument('--patients', type=int, default=55, help='Number of patients to create')
        parser.add_argument('--doctors', type=int, default=18, help='Number of doctors to create')
        parser.add_argument('--clean', action='store_true', help='Clean existing data before seeding')
    
    def handle(self, *args, **options):
        if options['clean']:
            self.clean_data()
        
        num_patients = options['patients']
        num_doctors = options['doctors']
        
        self.stdout.write(self.style.SUCCESS('🇲🇱 Starting Master Mali Pediatric Rehabilitation Demo Data...'))
        
        try:
            with transaction.atomic():
                # Create all demo data in proper dependency order
                facilities = self.create_facilities()
                self.create_facility_capabilities(facilities)
                doctors, pharmacists = self.create_medical_staff(num_doctors, facilities)
                medications = self.create_medication_database()
                icd10_codes = self.create_icd10_codes()
                patients = self.create_patients(num_patients, facilities)
                
                # Create medical data
                medical_records = self.create_medical_records(patients, doctors, facilities, icd10_codes)
                self.create_vital_signs(patients, medical_records)
                appointments = self.create_appointments(patients, doctors, facilities)
                prescriptions = self.create_prescriptions(patients, doctors, pharmacists, medications, facilities)
                vouchers = self.create_vouchers(patients, doctors, facilities)
                
                # Create TDR features
                hospitalizations = self.create_hospitalizations(patients, doctors, facilities)
                self.create_hospitalization_progress(hospitalizations, doctors)
                referrals = self.create_referrals(patients, doctors, facilities)
                self.create_referral_responses(referrals, doctors)
                self.create_inter_facility_communication(facilities, doctors)
                
                # Create rehabilitation data
                rehab_plans = self.create_rehabilitation_plans(patients, doctors)
                self.create_rehabilitation_sessions(rehab_plans, doctors)
                
                # Create demo users
                self.create_demo_users(facilities)
                
                # Create dashboard data
                self.create_security_audit_data()
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error creating demo data: {str(e)}'))
            raise e
        
        self.stdout.write(self.style.SUCCESS(f'🎉 Master Mali demo data created successfully!'))
        self.stdout.write(f'✅ {num_patients} patients, {num_doctors} doctors, {len(facilities)} facilities')
        self.stdout.write(f'✅ TDR Features: Hospitalizations, Referrals, Inter-facility Communication')
        self.stdout.write(f'✅ Dashboard ready with security & audit data')
    
    def clean_data(self):
        """Clean existing demo data"""
        self.stdout.write('🧹 Cleaning existing demo data...')
        
        # Delete in reverse dependency order
        DischargeReport.objects.all().delete()
        HospitalizationProgressNote.objects.all().delete()
        Hospitalization.objects.all().delete()
        ReferralFollowUp.objects.all().delete()
        ReferralResponse.objects.all().delete()
        Referral.objects.all().delete()
        InterFacilityCommunication.objects.all().delete()
        RehabilitationSession.objects.all().delete()
        RehabilitationPlan.objects.all().delete()
        PrescriptionMedication.objects.all().delete()
        Prescription.objects.all().delete()
        Voucher.objects.all().delete()
        Appointment.objects.all().delete()
        VitalSigns.objects.all().delete()
        MedicalRecord.objects.all().delete()
        Patient.objects.all().delete()
        
        # Clean users (keep admin users)
        User.objects.exclude(is_superuser=True).exclude(username__in=['admin', 'superadmin', 'facilityAdmin']).delete()
        
        self.stdout.write('✅ Data cleaned')
    
    def create_facilities(self):
        """Create comprehensive Mali healthcare facilities"""
        facilities_data = [
            {
                'name': 'CSREF Commune I',
                'facility_type': 'CSRef',
                'address': '123 Avenue de l\'Indépendance',
                'city': 'Bamako',
                'region': 'District de Bamako - Commune I',
                'phone': '+223 20212223',
                'email': 'csref1@sante.ml',
            },
            {
                'name': 'Centre de Réadaptation Pédiatrique Commune II',
                'facility_type': 'CR',
                'address': '45 Avenue du Mali, Badalabougou',
                'city': 'Bamako',
                'region': 'District de Bamako - Commune II',
                'phone': '+223 20232425',
                'email': 'crp2@humanite-inclusion.org',
            },
            {
                'name': 'CSREF Commune III',
                'facility_type': 'CSRef',
                'address': '78 Rue de la Solidarité',
                'city': 'Bamako',
                'region': 'District de Bamako - Commune III',
                'phone': '+223 20262728',
                'email': 'csref3@sante.ml',
            },
            {
                'name': 'CSCom Magnambougou',
                'facility_type': 'CSCom',
                'address': '12 Rue des Fleurs, Magnambougou',
                'city': 'Bamako',
                'region': 'District de Bamako - Commune IV',
                'phone': '+223 65666768',
                'email': 'cscom.magnambougou@sante.ml',
            },
            {
                'name': 'Centre Handicap International Commune V',
                'facility_type': 'CR',
                'address': '89 Boulevard de l\'Inclusion',
                'city': 'Bamako',
                'region': 'District de Bamako - Commune V',
                'phone': '+223 20353637',
                'email': 'centre.commune5@humanite-inclusion.org',
            },
            {
                'name': 'Hôpital Gabriel Touré - Pédiatrie',
                'facility_type': 'H',
                'address': 'Avenue de la Liberté',
                'city': 'Bamako',
                'region': 'District de Bamako - Commune VI',
                'phone': '+223 20293031',
                'email': 'pediatrie@hgt.sante.ml',
            },
            {
                'name': 'Centre National de Réadaptation Fonctionnelle',
                'facility_type': 'CR',
                'address': '156 Route de Koulikoro, ACI 2000',
                'city': 'Bamako',
                'region': 'District de Bamako - ACI',
                'phone': '+223 20404142',
                'email': 'cnrf@sante.ml',
            },
            {
                'name': 'Clinique Pasteur - Unité Pédiatrique',
                'facility_type': 'A',
                'address': '234 Avenue Cheick Zayed, Hippodrome',
                'city': 'Bamako',
                'region': 'District de Bamako - Hippodrome',
                'phone': '+223 20454647',
                'email': 'pediatrie@pasteur.ml',
            }
        ]
        
        facilities = []
        for f_data in facilities_data:
            facility, created = Facility.objects.get_or_create(
                name=f_data['name'],
                defaults=f_data
            )
            if created:
                self.stdout.write(f'🏥 Created facility: {facility.name}')
            facilities.append(facility)
        
        return facilities
    
    def create_facility_capabilities(self, facilities):
        """Create facility capabilities for TDR compliance"""
        capabilities_data = [
            # Rehabilitation centers
            {'name': 'rehabilitation', 'level': 'expert'},
            {'name': 'physiotherapy', 'level': 'advanced'},
            {'name': 'occupational_therapy', 'level': 'advanced'},
            {'name': 'speech_therapy', 'level': 'intermediate'},
            {'name': 'psychology', 'level': 'intermediate'},
            
            # General facilities
            {'name': 'pediatrics', 'level': 'advanced'},
            {'name': 'neurology', 'level': 'intermediate'},
            {'name': 'orthopedics', 'level': 'basic'},
            {'name': 'nutrition', 'level': 'basic'},
            {'name': 'social_work', 'level': 'basic'},
        ]
        
        for facility in facilities:
            # Rehabilitation centers get more capabilities
            if facility.facility_type == 'CR':
                selected_capabilities = capabilities_data[:8]
            else:
                selected_capabilities = random.sample(capabilities_data[5:], 3)
            
            for cap_data in selected_capabilities:
                FacilityCapability.objects.get_or_create(
                    facility=facility,
                    name=cap_data['name'],
                    defaults={
                        'capability_type': 'specialty',
                        'capacity_level': cap_data['level'],
                        'is_available': True,
                        'max_patients_per_day': random.randint(10, 50)
                    }
                )
        
        self.stdout.write('✅ Created facility capabilities')
    
    def create_medical_staff(self, num_doctors, facilities):
        """Create medical staff with Mali names and proper phone format"""
        first_names = ['Adama', 'Fatoumata', 'Ibrahim', 'Mariam', 'Oumar', 'Aminata', 'Moussa', 
                       'Kadiatou', 'Mamadou', 'Aïssata', 'Seydou', 'Oumou', 'Abdoulaye', 'Fanta', 
                       'Samba', 'Rokia', 'Boubacar', 'Assétou', 'Modibo', 'Hawa']
        last_names = ['Traoré', 'Diallo', 'Koné', 'Keita', 'Dembélé', 'Touré', 'Coulibaly', 
                      'Sangaré', 'Ballo', 'Cissé', 'Camara', 'Sidibé', 'Konaté', 'Doumbia', 
                      'Samaké', 'Sissoko', 'Maïga', 'Kané', 'Bagayoko', 'Diabaté']
        
        specialties = [
            'Pédiatrie générale', 'Neurologie pédiatrique', 'Physiothérapie pédiatrique',
            'Orthophonie', 'Kinésithérapie', 'Ergothérapie', 'Psychologie pédiatrique',
            'Nutrition pédiatrique', 'Orthopédie pédiatrique', 'Cardiologie pédiatrique'
        ]
        
        doctors = []
        pharmacists = []
        
        # Create doctors
        for i in range(num_doctors):
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            username = f"dr.{first_name.lower()}.{last_name.lower()}.{i+1}"
            
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'email': f"{username}@sante.ml"
                }
            )
            
            if created:
                user.set_password('demo1234')
                user.save()
                
                # PostgreSQL-compatible phone format (max 15 chars)
                phone = f'+223{random.randint(60000000, 79999999)}'  # 13 chars total
                
                user_profile = user.profile
                user_profile.user_type = 'doctor'
                user_profile.phone_number = phone
                user_profile.facility = random.choice(facilities)
                user_profile.save()
                
                doctors.append(user_profile)
                specialty = random.choice(specialties)
                self.stdout.write(f'👨‍⚕️ Created doctor: Dr. {first_name} {last_name} ({specialty})')
        
        # Create pharmacists
        num_pharmacists = max(3, num_doctors // 4)
        for i in range(num_pharmacists):
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            username = f"pharm.{first_name.lower()}.{last_name.lower()}.{i+1}"
            
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'email': f"{username}@sante.ml"
                }
            )
            
            if created:
                user.set_password('demo1234')
                user.save()
                
                phone = f'+223{random.randint(60000000, 79999999)}'
                
                user_profile = user.profile
                user_profile.user_type = 'pharmacist'
                user_profile.phone_number = phone
                user_profile.facility = random.choice(facilities)
                user_profile.save()
                
                pharmacists.append(user_profile)
                self.stdout.write(f'💊 Created pharmacist: {first_name} {last_name}')
        
        return doctors, pharmacists
    
    def create_medication_database(self):
        """Create Mali-available pediatric medications"""
        # Create categories first
        categories_data = [
            {'name': 'Antibiotiques pédiatriques', 'description': 'Antibiotics for children'},
            {'name': 'Antipaludéens', 'description': 'Antimalarial medications'},
            {'name': 'Vitamines et suppléments', 'description': 'Vitamins and supplements'},
            {'name': 'Antalgiques pédiatriques', 'description': 'Pain relief for children'},
            {'name': 'Nutrition thérapeutique', 'description': 'Therapeutic nutrition'},
            {'name': 'Anticonvulsivants', 'description': 'Anti-seizure medications'},
        ]
        
        for cat_data in categories_data:
            MedicationCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults=cat_data
            )
        
        # Create medications
        medications_data = [
            {'name': 'Amoxicilline sirop 125mg/5ml', 'category': 'Antibiotiques pédiatriques', 'form': 'SYRUP'},
            {'name': 'Artéméther + Luméfantrine', 'category': 'Antipaludéens', 'form': 'TABLET'},
            {'name': 'Vitamine A 200,000 UI', 'category': 'Vitamines et suppléments', 'form': 'CAPSULE'},
            {'name': 'Paracétamol sirop 120mg/5ml', 'category': 'Antalgiques pédiatriques', 'form': 'SYRUP'},
            {'name': 'Plumpy\'Nut (RUTF)', 'category': 'Nutrition thérapeutique', 'form': 'OTHER'},
            {'name': 'Phénobarbital sirop', 'category': 'Anticonvulsivants', 'form': 'SYRUP'},
        ]
        
        medications = []
        for med_data in medications_data:
            try:
                category = MedicationCategory.objects.get(name=med_data['category'])
                medication, created = Medication.objects.get_or_create(
                    name=med_data['name'],
                    defaults={
                        'category': category,
                        'form': med_data['form'],
                        'is_pediatric_approved': True,
                        'available_in_mali': True
                    }
                )
                if created:
                    medications.append(medication)
            except MedicationCategory.DoesNotExist:
                continue
        
        self.stdout.write(f'💊 Created {len(medications)} medications')
        return medications
    
    def create_icd10_codes(self):
        """Create ICD-10 codes for pediatric disabilities"""
        icd10_data = [
            {'code': 'F70', 'title': 'Retard mental léger', 'category': 'F00-F99'},
            {'code': 'F84.0', 'title': 'Autisme infantile', 'category': 'F00-F99'},
            {'code': 'G80.1', 'title': 'Paralysie cérébrale spastique diplégique', 'category': 'G00-G99'},
            {'code': 'G80.2', 'title': 'Paralysie cérébrale spastique hémiplégique', 'category': 'G00-G99'},
            {'code': 'H54.0', 'title': 'Cécité, binoculaire', 'category': 'H00-H59'},
            {'code': 'H90.3', 'title': 'Surdité de perception, bilatérale', 'category': 'H60-H95'},
            {'code': 'E43', 'title': 'Malnutrition protéino-énergétique grave', 'category': 'OTHER'},
            {'code': 'Q05.9', 'title': 'Spina bifida, sans précision', 'category': 'Q00-Q99'},
        ]
        
        icd10_codes = []
        for icd_data in icd10_data:
            icd10_code, created = ICD10Code.objects.get_or_create(
                code=icd_data['code'],
                defaults={
                    **icd_data,
                    'description': f'Diagnostic pédiatrique: {icd_data["title"]}',
                    'is_pediatric_relevant': True,
                    'is_disability_related': True
                }
            )
            icd10_codes.append(icd10_code)
        
        self.stdout.write(f'🏷️ Created {len(icd10_codes)} ICD-10 codes')
        return icd10_codes
    
    def create_patients(self, num_patients, facilities):
        """Create Mali children with PostgreSQL-compatible constraints"""
        child_names = ['Ibrahim', 'Fatoumata', 'Mamadou', 'Aïssata', 'Oumar', 'Aminata', 
                       'Adama', 'Fanta', 'Seydou', 'Mariam', 'Moussa', 'Kadiatou']
        last_names = ['Traoré', 'Diallo', 'Koné', 'Keita', 'Dembélé', 'Touré', 'Coulibaly', 
                      'Sangaré', 'Ballo', 'Cissé', 'Camara', 'Sidibé']
        
        districts = [
            'Commune I', 'Commune II', 'Commune III', 
            'Commune IV', 'Commune V', 'Commune VI'
        ]
        
        patients = []
        for i in range(num_patients):
            first_name = random.choice(child_names)
            last_name = random.choice(last_names)
            
            # Age 0-14 years (TDR requirement)
            age = random.randint(0, 14)
            today = datetime.date.today()
            date_of_birth = today - datetime.timedelta(days=age*365 + random.randint(0, 364))
            
            district = random.choice(districts)
            
            # PostgreSQL-compatible phone format
            guardian_phone = f'+223{random.randint(60000000, 79999999)}'
            
            # Create user
            username = f"patient.{first_name.lower()}.{last_name.lower()}.{i+1}"
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'email': f"{username}@example.com"
                }
            )
            
            if created:
                user.set_password('demo1234')
                user.save()
                
                user_profile = user.profile
                user_profile.user_type = 'patient'
                user_profile.save()
            
            # Generate patient ID
            import hashlib
            patient_id = f"P-{hashlib.md5(f'{first_name}{last_name}{date_of_birth}'.encode()).hexdigest()[:8].upper()}"
            
            patient, created = Patient.objects.get_or_create(
                user=user,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'date_of_birth': date_of_birth,
                    'gender': random.choice(['M', 'F']),
                    'address': f"{random.randint(1, 200)} {district}, Bamako",
                    'phone_number': guardian_phone,
                    'guardian_name': f"{random.choice(child_names)} {last_name}",
                    'guardian_phone': guardian_phone,
                    'patient_id': patient_id,
                    'city': 'Bamako',
                    'region': f'District de Bamako - {district}'
                }
            )
            
            if created:
                patients.append(patient)
                self.stdout.write(f'👶 Created patient: {first_name} {last_name}, age {age} ({district})')
        
        return patients
    
    def create_medical_records(self, patients, doctors, facilities, icd10_codes):
        """Create medical records with ICD-10 coding"""
        medical_records = []
        for patient in patients:
            num_records = random.randint(1, 3)
            for i in range(num_records):
                doctor = random.choice(doctors)
                facility = doctor.facility or random.choice(facilities)
                
                days_ago = random.randint(30, 365)
                record_date = timezone.now() - datetime.timedelta(days=days_ago)
                
                primary_diagnosis = random.choice(icd10_codes)
                
                record = MedicalRecord.objects.create(
                    patient=patient,
                    doctor=doctor,
                    facility=facility,
                    date=record_date,
                    primary_diagnosis_icd10=primary_diagnosis,
                    chief_complaint=f"Consultation pour {primary_diagnosis.title}",
                    present_illness="Présente des difficultés de développement nécessitant une prise en charge spécialisée.",
                    physical_examination="Examen physique révélant des signes compatibles avec le diagnostic.",
                    treatment_plan="Plan de prise en charge multidisciplinaire recommandé.",
                    recommendations="Suivi régulier et rééducation fonctionnelle."
                )
                medical_records.append(record)
        
        self.stdout.write(f'📋 Created {len(medical_records)} medical records')
        return medical_records
    
    def create_vital_signs(self, patients, medical_records):
        """Create vital signs data"""
        for record in medical_records:
            if not hasattr(record, 'vital_signs'):
                # Age-appropriate vital signs
                age_days = (record.date.date() - record.patient.date_of_birth).days
                age_months = age_days / 30.44
                
                if age_months < 12:  # Infant
                    height, weight, heart_rate = 65, 7, 130
                elif age_months < 60:  # Toddler
                    height, weight, heart_rate = 90, 14, 115
                else:  # Child
                    height, weight, heart_rate = 130, 35, 95
                
                VitalSigns.objects.create(
                    medical_record=record,
                    height=Decimal(str(height + random.uniform(-10, 10))),
                    weight=Decimal(str(weight + random.uniform(-2, 5))),
                    heart_rate=heart_rate + random.randint(-20, 20),
                    temperature=Decimal(str(round(random.uniform(36.5, 37.2), 1))),
                    respiratory_rate=random.randint(15, 30)
                )
        
        self.stdout.write('📊 Created vital signs data')
    
    def create_appointments(self, patients, doctors, facilities):
        """Create appointments"""
        appointments = []
        today = timezone.now().date()
        
        for patient in patients:
            num_appointments = random.randint(1, 4)
            for i in range(num_appointments):
                doctor = random.choice(doctors)
                facility = doctor.facility or random.choice(facilities)
                
                if random.random() < 0.6:  # Future
                    days_ahead = random.randint(1, 60)
                    appointment_date = today + datetime.timedelta(days=days_ahead)
                    status = random.choice(['scheduled', 'confirmed'])
                else:  # Past
                    days_ago = random.randint(1, 180)
                    appointment_date = today - datetime.timedelta(days=days_ago)
                    status = random.choice(['completed', 'completed', 'cancelled'])
                
                hour = random.randint(8, 16)
                minute = random.choice([0, 15, 30, 45])
                appointment_datetime = timezone.make_aware(
                    datetime.datetime.combine(appointment_date, datetime.time(hour, minute))
                )
                
                appointment = Appointment.objects.create(
                    patient=patient,
                    doctor=doctor,
                    facility=facility,
                    appointment_date=appointment_datetime,
                    reason=random.choice(['Suivi régulier', 'Évaluation développement', 'Rééducation']),
                    status=status
                )
                appointments.append(appointment)
        
        self.stdout.write(f'📅 Created {len(appointments)} appointments')
        return appointments
    
    def create_prescriptions(self, patients, doctors, pharmacists, medications, facilities):
        """Create prescriptions"""
        prescriptions = []
        for patient in random.sample(patients, k=int(len(patients) * 0.4)):
            doctor = random.choice(doctors)
            
            prescription = Prescription.objects.create(
                patient=patient,
                prescribing_doctor=doctor,
                prescribing_facility=doctor.facility,
                diagnosis="Prescription pédiatrique",
                status=random.choice(['PRESCRIBED', 'VALIDATED', 'DISPENSED']),
                priority='NORMAL'
            )
            
            # Add medications
            for _ in range(random.randint(1, 2)):
                if medications:
                    medication = random.choice(medications)
                    PrescriptionMedication.objects.create(
                        prescription=prescription,
                        medication=medication,
                        dose="Selon âge et poids",
                        frequency="2 fois par jour",
                        duration_days=random.randint(7, 30)
                    )
            
            prescriptions.append(prescription)
        
        self.stdout.write(f'💊 Created {len(prescriptions)} prescriptions')
        return prescriptions
    
    def create_vouchers(self, patients, doctors, facilities):
        """Create vouchers for HI workflow"""
        vouchers = []
        for patient in random.sample(patients, k=int(len(patients) * 0.7)):
            issuing_doctor = random.choice(doctors)
            target_facility = random.choice(facilities)
            
            issue_date = timezone.now().date() - datetime.timedelta(days=random.randint(1, 90))
            expiry_date = issue_date + datetime.timedelta(days=180)
            
            voucher = Voucher.objects.create(
                patient=patient,
                issuing_doctor=issuing_doctor,
                target_facility=target_facility,
                service_type="Réhabilitation pédiatrique",
                description=f"Bon pour rééducation enfant {patient.first_name}",
                issue_date=issue_date,
                expiry_date=expiry_date,
                status=random.choice(['issued', 'validated', 'used'])
            )
            vouchers.append(voucher)
        
        self.stdout.write(f'🎫 Created {len(vouchers)} vouchers')
        return vouchers
    
    def create_hospitalizations(self, patients, doctors, facilities):
        """Create TDR hospitalization data"""
        hospitalizations = []
        
        # Mali pediatric service types
        service_types = [
            'Pédiatrie A', 'Pédiatrie B', 'Réadaptation pédiatrique', 
            'Neurologie pédiatrique', 'Chirurgie pédiatrique', 'Soins intensifs pédiatriques'
        ]
        
        room_types = [
            'Chambre individuelle', 'Chambre double', 'Salle commune', 
            'Unité de soins intensifs', 'Salle de réadaptation'
        ]
        
        for patient in random.sample(patients, k=int(len(patients) * 0.3)):
            doctor = random.choice(doctors)
            facility = doctor.facility or random.choice(facilities)
            
            admission_date = timezone.now().date() - datetime.timedelta(days=random.randint(1, 180))
            
            # 70% discharged, 30% still admitted
            if random.random() < 0.7:
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
                admission_reason=f"Hospitalisation pour {random.choice(['réadaptation', 'observation', 'traitement spécialisé'])}",
                admission_diagnosis=f"Diagnostic pédiatrique - {patient.first_name}",
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
        progress_notes = []
        
        for hospitalization in hospitalizations:
            # Create 2-5 progress notes per hospitalization
            num_notes = random.randint(2, 5)
            
            start_date = hospitalization.admission_date
            end_date = hospitalization.discharge_date or timezone.now().date()
            
            for i in range(num_notes):
                note_date = start_date + datetime.timedelta(
                    days=i * ((end_date - start_date).days // num_notes if num_notes > 1 else 1)
                )
                
                note = HospitalizationProgressNote.objects.create(
                    hospitalization=hospitalization,
                    date=note_date,
                    doctor=random.choice(doctors),
                    clinical_notes=f"Évolution favorable du patient {hospitalization.patient.first_name}. Poursuite du traitement.",
                    vital_signs_notes=f"Signes vitaux stables. Température: {random.uniform(36.5, 37.2):.1f}°C",
                    treatment_notes="Traitement adapté selon l'évolution clinique.",
                    plan_notes="Plan de soins maintenu avec surveillance renforcée."
                )
                progress_notes.append(note)
        
        self.stdout.write(f'📝 Created {len(progress_notes)} progress notes')
    
    def create_referrals(self, patients, doctors, facilities):
        """Create inter-facility referrals (TDR requirement)"""
        referrals = []
        
        referral_types = [
            'consultation', 'rehabilitation', 'surgery', 'diagnostic', 'follow_up'
        ]
        
        for patient in random.sample(patients, k=int(len(patients) * 0.4)):
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
                referral_reason=f"Référence pour soins spécialisés - {patient.first_name}",
                medical_summary=f"Patient nécessitant une prise en charge spécialisée en {random.choice(['neurologie', 'orthopédie', 'réadaptation'])}",
                urgency_level=random.choice(['normal', 'high', 'urgent']),
                preferred_date=referral_date + datetime.timedelta(days=random.randint(1, 30)),
                status=random.choice(['pending', 'accepted', 'completed']),
                referral_date=referral_date
            )
            referrals.append(referral)
        
        self.stdout.write(f'🔄 Created {len(referrals)} inter-facility referrals')
        return referrals
    
    def create_referral_responses(self, referrals, doctors):
        """Create referral responses"""
        responses = []
        
        for referral in referrals:
            if referral.status in ['accepted', 'completed']:
                # Find doctor at receiving facility
                receiving_doctors = [d for d in doctors if d.facility == referral.receiving_facility]
                if receiving_doctors:
                    receiving_doctor = random.choice(receiving_doctors)
                    
                    response = ReferralResponse.objects.create(
                        referral=referral,
                        responding_doctor=receiving_doctor,
                        response_date=referral.referral_date + datetime.timedelta(days=random.randint(1, 7)),
                        response_status='accepted' if referral.status == 'accepted' else 'completed',
                        response_notes=f"Référence acceptée pour {referral.patient.first_name}. RDV programmé.",
                        proposed_appointment_date=referral.preferred_date + datetime.timedelta(days=random.randint(1, 14))
                    )
                    responses.append(response)
        
        self.stdout.write(f'📨 Created {len(responses)} referral responses')
    
    def create_inter_facility_communication(self, facilities, doctors):
        """Create inter-facility communications (TDR requirement)"""
        communications = []
        
        communication_types = [
            'patient_referral', 'resource_sharing', 'information_request', 
            'coordination', 'emergency_notification', 'administrative'
        ]
        
        message_templates = {
            'patient_referral': "Référence patient {} pour soins spécialisés",
            'resource_sharing': "Demande de partage d'équipement médical",
            'information_request': "Demande d'information sur protocole de soins",
            'coordination': "Coordination pour prise en charge multidisciplinaire",
            'emergency_notification': "Notification urgente - patient critique",
            'administrative': "Communication administrative inter-établissements"
        }
        
        # Create 50+ communications between facilities
        for _ in range(random.randint(50, 75)):
            sending_facility = random.choice(facilities)
            receiving_facility = random.choice([f for f in facilities if f != sending_facility])
            sender = random.choice([d for d in doctors if d.facility == sending_facility] or doctors)
            
            comm_type = random.choice(communication_types)
            
            communication = InterFacilityCommunication.objects.create(
                sending_facility=sending_facility,
                receiving_facility=receiving_facility,
                sender=sender,
                communication_type=comm_type,
                subject=f"Communication {comm_type.replace('_', ' ').title()}",
                message=message_templates[comm_type].format(random.choice(['Ibrahim', 'Fatoumata', 'Mamadou'])),
                urgency_level=random.choice(['low', 'normal', 'high']),
                status=random.choice(['sent', 'delivered', 'read', 'responded']),
                sent_date=timezone.now() - datetime.timedelta(days=random.randint(1, 90))
            )
            communications.append(communication)
        
        self.stdout.write(f'💬 Created {len(communications)} inter-facility communications')
    
    def create_rehabilitation_plans(self, patients, doctors):
        """Create rehabilitation plans"""
        rehab_plans = []
        
        for patient in random.sample(patients, k=int(len(patients) * 0.6)):
            doctor = random.choice(doctors)
            start_date = timezone.now().date() - datetime.timedelta(days=random.randint(30, 180))
            
            try:
                plan = RehabilitationPlan.objects.create(
                    patient=patient,
                    prescribing_doctor=doctor,
                    start_date=start_date,
                    diagnosis=f"Plan de réadaptation pour {patient.first_name}",
                    goals="Amélioration des capacités fonctionnelles et de l'autonomie",
                    status='active'
                )
                rehab_plans.append(plan)
            except Exception as e:
                # Skip if rehabilitation model has schema issues
                continue
        
        self.stdout.write(f'🏋️ Created {len(rehab_plans)} rehabilitation plans')
        return rehab_plans
    
    def create_rehabilitation_sessions(self, rehab_plans, doctors):
        """Create rehabilitation sessions"""
        sessions = []
        
        session_types = [
            'Kinésithérapie', 'Ergothérapie', 'Orthophonie', 
            'Soutien psychologique', 'Éducation familiale'
        ]
        
        for plan in rehab_plans:
            num_sessions = random.randint(5, 15)
            
            for i in range(num_sessions):
                session_date = plan.start_date + datetime.timedelta(days=i * 7)  # Weekly sessions
                
                try:
                    session = RehabilitationSession.objects.create(
                        plan=plan,
                        session_date=session_date,
                        duration_minutes=random.randint(30, 90),
                        notes=f"Séance de {random.choice(session_types)} pour {plan.patient.first_name}",
                        status=random.choice(['scheduled', 'completed', 'cancelled'])
                    )
                    sessions.append(session)
                except Exception as e:
                    continue
        
        self.stdout.write(f'🏃‍♂️ Created {len(sessions)} rehabilitation sessions')
    
    def create_demo_users(self, facilities):
        """Create demo users for login"""
        demo_users = [
            {'username': 'superadmin', 'user_type': 'superadmin', 'facility': None},
            {'username': 'facilityAdmin', 'user_type': 'facility_admin', 'facility': facilities[0] if facilities else None},
            {'username': 'docteur', 'user_type': 'doctor', 'facility': facilities[1] if len(facilities) > 1 else facilities[0]},
            {'username': 'patient', 'user_type': 'patient', 'facility': None},
        ]
        
        for user_data in demo_users:
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={
                    'first_name': user_data['username'].title(),
                    'last_name': 'Demo',
                    'email': f"{user_data['username']}@demo.ml",
                    'is_staff': True if user_data['user_type'] == 'superadmin' else False,
                    'is_superuser': True if user_data['user_type'] == 'superadmin' else False
                }
            )
            
            if created:
                user.set_password('demo1234')
                user.save()
            
            # Update profile
            profile = user.profile
            profile.user_type = user_data['user_type']
            profile.facility = user_data['facility']
            profile.phone_number = f'+223{random.randint(60000000, 79999999)}'
            profile.save()
        
        self.stdout.write('👤 Created demo users')
    
    def create_security_audit_data(self):
        """Create security and audit data for dashboards"""
        try:
            # Create some system activities
            activities = [
                'user_login', 'patient_created', 'appointment_scheduled', 
                'prescription_created', 'referral_sent', 'communication_sent'
            ]
            
            for _ in range(100):  # Create 100 activities
                SystemActivity.objects.create(
                    user=User.objects.order_by('?').first(),
                    activity_type=random.choice(activities),
                    description=f"Activité système: {random.choice(activities)}",
                    ip_address=f"192.168.1.{random.randint(1, 254)}",
                    timestamp=timezone.now() - datetime.timedelta(days=random.randint(1, 30))
                )
            
            self.stdout.write('🔒 Created security audit data')
        except Exception as e:
            self.stdout.write(f'⚠️ Skipped security data: {str(e)}') 