import datetime
import random
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from accounts.models import UserProfile
from patients.models import Patient, MedicalRecord
from appointments.models import Appointment
from facilities.models import Facility
from rehabilitation.models import RehabilitationPlan, RehabilitationSession
from vouchers.models import Voucher

class Command(BaseCommand):
    help = 'Seed database with realistic Mali healthcare demo data'
    
    def add_arguments(self, parser):
        parser.add_argument('--patients', type=int, default=30, help='Number of patients to create')
        parser.add_argument('--doctors', type=int, default=10, help='Number of doctors to create')
        parser.add_argument('--clean', action='store_true', help='Clean existing data before seeding')
    
    def handle(self, *args, **options):
        if options['clean']:
            self.clean_data()
        
        num_patients = options['patients']
        num_doctors = options['doctors']
        
        self.stdout.write(self.style.SUCCESS('Starting data seeding...'))
        
        # Create facilities
        facilities = self.create_facilities()
        
        # Create users and user profiles
        doctors = self.create_medical_staff(num_doctors, facilities)
        
        # Create patients
        patients = self.create_patients(num_patients)
        
        # Create medical records, appointments, rehabilitation plans, and vouchers
        self.create_medical_records(patients, doctors, facilities)
        self.create_appointments(patients, doctors, facilities)
        self.create_rehabilitation_plans(patients, doctors)
        self.create_vouchers(patients, doctors, facilities)
        
        self.stdout.write(self.style.SUCCESS(f'Successfully seeded the database with demo data!'))
        self.stdout.write(f'Created {num_patients} patients, {num_doctors} doctors, and {len(facilities)} facilities')
    
    def clean_data(self):
        """Clean existing demo data"""
        self.stdout.write('Cleaning existing data...')
        Voucher.objects.all().delete()
        RehabilitationSession.objects.all().delete()
        RehabilitationPlan.objects.all().delete()
        Appointment.objects.all().delete()
        MedicalRecord.objects.all().delete()
        Patient.objects.all().delete()
        
        # Don't delete UserProfile objects with user_types superadmin or facility_admin
        UserProfile.objects.filter(user_type__in=['doctor', 'patient']).delete()
        
        # Don't delete the main demo users
        demo_users = ['superadmin', 'facilityAdmin', 'docteur', 'patient']
        users_to_delete = User.objects.exclude(username__in=demo_users)
        users_to_delete.delete()
        
        self.stdout.write(self.style.SUCCESS('Data cleaned successfully!'))
    
    def create_facilities(self):
        """Create healthcare facilities in Mali"""
        facilities_data = [
            {
                'name': 'CSREF Commune I',
                'facility_type': 'CSRef',
                'address': '123 Avenue de l\'Indépendance',
                'city': 'Bamako',
                'region': 'District de Bamako',
                'phone': '+223 20 21 22 23',
                'email': 'csref1@sante.ml',
                'year_established': 1998
            },
            {
                'name': 'CSREF Commune III',
                'facility_type': 'CSRef',
                'address': '45 Avenue du Mali',
                'city': 'Bamako',
                'region': 'District de Bamako',
                'phone': '+223 20 23 24 25',
                'email': 'csref3@sante.ml',
                'year_established': 2001
            },
            {
                'name': 'Centre de Réadaptation Nationale',
                'facility_type': 'CR',
                'address': '78 Rue de la Solidarité',
                'city': 'Bamako',
                'region': 'District de Bamako',
                'phone': '+223 20 26 27 28',
                'email': 'cran@sante.ml',
                'year_established': 2010
            },
            {
                'name': 'CSCom Magnambougou',
                'facility_type': 'CSCom',
                'address': '12 Rue des Fleurs, Magnambougou',
                'city': 'Bamako',
                'region': 'District de Bamako',
                'phone': '+223 65 66 67 68',
                'email': 'cscom.magnambougou@sante.ml',
                'year_established': 2005
            },
            {
                'name': 'Hôpital Gabriel Touré',
                'facility_type': 'H',
                'address': 'Avenue de la Liberté',
                'city': 'Bamako',
                'region': 'District de Bamako',
                'phone': '+223 20 29 30 31',
                'email': 'hgt@sante.ml',
                'year_established': 1959
            }
        ]
        
        facilities = []
        for f_data in facilities_data:
            facility, created = Facility.objects.get_or_create(
                name=f_data['name'],
                defaults=f_data
            )
            if created:
                self.stdout.write(f'Created facility: {facility.name}')
            facilities.append(facility)
        
        return facilities
    
    def create_medical_staff(self, num_doctors, facilities):
        """Create doctor user profiles"""
        # Mali common names
        first_names = ['Adama', 'Fatoumata', 'Ibrahim', 'Mariam', 'Oumar', 'Aminata', 'Moussa', 
                       'Kadiatou', 'Mamadou', 'Aïssata', 'Seydou', 'Oumou', 'Abdoulaye', 'Fanta', 'Samba']
        last_names = ['Traoré', 'Diallo', 'Koné', 'Keita', 'Dembélé', 'Touré', 'Coulibaly', 
                      'Sangaré', 'Ballo', 'Cissé', 'Camara', 'Sidibé', 'Konaté', 'Doumbia', 'Samaké']
        specialties = ['Pédiatrie', 'Physiothérapie', 'Orthophonie', 'Kinésithérapie', 'Neurologie',
                       'Médecine générale', 'Orthopédie', 'Ergothérapie', 'Psychologie', 'Nutrition']
        
        doctors = []
        for i in range(num_doctors):
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            username = f"dr.{first_name.lower()}.{last_name.lower()}"
            
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
                
                user_profile = UserProfile.objects.get(user=user)
                user_profile.user_type = 'doctor'
                user_profile.phone_number = f'+223 7{random.randint(0, 9)} {random.randint(10, 99)} {random.randint(10, 99)} {random.randint(10, 99)}'
                user_profile.facility = random.choice(facilities)
                user_profile.save()
                
                doctors.append(user_profile)
                self.stdout.write(f'Created doctor: {first_name} {last_name}')
        
        return doctors
    
    def create_patients(self, num_patients):
        """Create patient records"""
        # Mali common names
        child_first_names = ['Ibrahim', 'Fatoumata', 'Mamadou', 'Aïssata', 'Oumar', 'Aminata', 
                             'Adama', 'Fanta', 'Seydou', 'Mariam', 'Moussa', 'Kadiatou', 'Abdoulaye', 'Oumou', 'Samba']
        last_names = ['Traoré', 'Diallo', 'Koné', 'Keita', 'Dembélé', 'Touré', 'Coulibaly', 
                      'Sangaré', 'Ballo', 'Cissé', 'Camara', 'Sidibé', 'Konaté', 'Doumbia', 'Samaké']
        
        # Communes in Bamako
        addresses = [
            'Quartier du Fleuve, Bamako',
            'Badalabougou, Bamako',
            'Magnambougou, Bamako',
            'Kalaban Coura, Bamako',
            'Hamdallaye, Bamako',
            'Lafiabougou, Bamako',
            'Djicoroni Para, Bamako',
            'Sogoniko, Bamako',
            'Médina Coura, Bamako',
            'Quinzambougou, Bamako'
        ]
        
        # Common conditions for children in Mali that might require rehabilitation
        conditions = [
            'Paralysie cérébrale',
            'Retard de développement',
            'Malnutrition sévère',
            'Séquelles de paludisme cérébral',
            'Handicap congénital',
            'Traumatisme crânien',
            'Polyhandicap',
            'Déficit moteur',
            'Trouble du spectre autistique',
            'Pied bot',
            'Séquelles de méningite',
            'Déficience visuelle',
            'Déficience auditive',
            'Malformation congénitale',
            'Handicap post-infection'
        ]
        
        patients = []
        for i in range(num_patients):
            first_name = random.choice(child_first_names)
            last_name = random.choice(last_names)
            gender = random.choice(['M', 'F'])
            
            # Age between 0-14 years (target demographic)
            age = random.randint(0, 14)
            today = datetime.date.today()
            date_of_birth = today - datetime.timedelta(days=age*365 + random.randint(0, 364))
            
            # Create a user for the patient (for login purposes)
            username = f"patient.{first_name.lower()}.{last_name.lower()}"
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
                
                user_profile = UserProfile.objects.get(user=user)
                user_profile.user_type = 'patient'
                user_profile.save()
            
            # Generate a unique patient ID
            import hashlib
            patient_id = f"P-{hashlib.md5(f'{first_name}{last_name}{date_of_birth}'.encode()).hexdigest()[:8].upper()}"
            
            # Create guardian (parent) name
            if gender == 'M':
                guardian_first_name = 'Adama' if random.choice([True, False]) else 'Ibrahim'
            else:
                guardian_first_name = 'Fatoumata' if random.choice([True, False]) else 'Mariam'
            
            guardian_name = f"{guardian_first_name} {last_name}"
            guardian_phone = f'+223 7{random.randint(0, 9)} {random.randint(10, 99)} {random.randint(10, 99)} {random.randint(10, 99)}'
            
            # Create the patient
            patient, created = Patient.objects.get_or_create(
                user=user,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'date_of_birth': date_of_birth,
                    'gender': gender,
                    'address': random.choice(addresses),
                    'phone_number': guardian_phone,
                    'guardian_name': guardian_name,
                    'guardian_phone': guardian_phone,
                    'patient_id': patient_id
                }
            )
            
            if created:
                patients.append(patient)
                self.stdout.write(f'Created patient: {first_name} {last_name}, age {age}')
        
        return patients
    
    def create_medical_records(self, patients, doctors, facilities):
        """Create medical records for patients"""
        for patient in patients:
            # Create 1-3 medical records per patient
            num_records = random.randint(1, 3)
            
            for i in range(num_records):
                doctor = random.choice(doctors)
                facility = random.choice(facilities)
                
                # Date of record (random date between 1 month and 1 year ago)
                days_ago = random.randint(30, 365)
                record_date = timezone.now() - datetime.timedelta(days=days_ago)
                
                # Common diagnoses for children in Mali requiring rehabilitation
                diagnoses = [
                    'Paralysie cérébrale',
                    'Retard de développement',
                    'Malnutrition',
                    'Séquelles de paludisme cérébral',
                    'Handicap moteur',
                    'Traumatisme crânien',
                    'Polyhandicap',
                    'Déficit moteur',
                    'Trouble du spectre autistique',
                    'Pied bot',
                    'Séquelles de méningite'
                ]
                
                diagnosis = random.choice(diagnoses)
                
                descriptions = {
                    'Paralysie cérébrale': 'Présente une rigidité musculaire et des difficultés de mouvement. Nécessite une prise en charge rééducative régulière.',
                    'Retard de développement': 'Retard par rapport aux étapes de développement normales. Nécessite une stimulation précoce et un suivi régulier.',
                    'Malnutrition': 'État nutritionnel déficient ayant entraîné des séquelles développementales. Programme de réhabilitation nutritionnelle en cours.',
                    'Séquelles de paludisme cérébral': 'Présente des difficultés motrices et cognitives suite à un paludisme cérébral. Plan de rééducation multidisciplinaire recommandé.',
                    'Handicap moteur': 'Difficultés de motricité fine et globale nécessitant une prise en charge en kinésithérapie.',
                    'Traumatisme crânien': 'Séquelles d\'un accident entraînant des troubles de l\'équilibre et de la coordination. Rééducation fonctionnelle indiquée.',
                    'Polyhandicap': 'Association de déficiences motrices et intellectuelles nécessitant une prise en charge globale.',
                    'Déficit moteur': 'Faiblesse musculaire du membre inférieur droit suite à une infection. Programme de renforcement recommandé.',
                    'Trouble du spectre autistique': 'Difficultés de communication et d\'interactions sociales. Thérapie comportementale et orthophonie indiquées.',
                    'Pied bot': 'Déformation congénitale du pied nécessitant une prise en charge orthopédique et rééducative.',
                    'Séquelles de méningite': 'Déficit auditif et troubles de l\'équilibre suite à une méningite. Rééducation vestibulaire recommandée.'
                }
                
                recommendations = {
                    'Paralysie cérébrale': 'Séances de kinésithérapie 3x/semaine. Évaluation orthopédique dans 3 mois. Adaptation de l\'environnement familial.',
                    'Retard de développement': 'Programme de stimulation précoce. Séances d\'ergothérapie 2x/semaine. Guidance parentale.',
                    'Malnutrition': 'Suivi nutritionnel hebdomadaire. Supplémentation en vitamines et minéraux. Exercices de renforcement progressif.',
                    'Séquelles de paludisme cérébral': 'Prise en charge multidisciplinaire : kinésithérapie, orthophonie et suivi neurologique trimestriel.',
                    'Handicap moteur': 'Physiothérapie 2x/semaine. Exercices quotidiens à domicile selon programme fourni.',
                    'Traumatisme crânien': 'Rééducation neurologique intensive. Suivi psychologique. Évaluation cognitive à prévoir.',
                    'Polyhandicap': 'Prise en charge globale : kinésithérapie, orthophonie, ergothérapie. Formation des aidants familiaux.',
                    'Déficit moteur': 'Programme de renforcement musculaire progressif. Séances de kinésithérapie 2x/semaine.',
                    'Trouble du spectre autistique': 'Thérapie comportementale structurée. Orthophonie 2x/semaine. Soutien éducatif adapté.',
                    'Pied bot': 'Suivi orthopédique mensuel. Port d\'orthèses. Exercices d\'étirement quotidiens.',
                    'Séquelles de méningite': 'Évaluation audiologique complète. Rééducation vestibulaire 2x/semaine. Suivi ORL.'
                }
                
                record = MedicalRecord.objects.create(
                    patient=patient,
                    doctor=doctor,
                    facility=facility,
                    date=record_date,
                    diagnosis=diagnosis,
                    description=descriptions.get(diagnosis, 'Description non disponible'),
                    recommendations=recommendations.get(diagnosis, 'Recommandations à définir')
                )
                
        self.stdout.write(f'Created medical records for {len(patients)} patients')
    
    def create_appointments(self, patients, doctors, facilities):
        """Create appointments for patients"""
        # Create some past appointments and some upcoming appointments
        today = timezone.now().date()
        
        for patient in patients:
            # Create 1-3 appointments per patient
            num_appointments = random.randint(1, 3)
            
            for i in range(num_appointments):
                doctor = random.choice(doctors)
                facility = doctor.facility or random.choice(facilities)
                
                # 60% chance of future appointment, 40% chance of past appointment
                if random.random() < 0.6:
                    # Future appointment (within next 30 days)
                    days_ahead = random.randint(1, 30)
                    appointment_date = today + datetime.timedelta(days=days_ahead)
                    status = 'scheduled'
                    if random.random() < 0.3:  # 30% of future appointments are confirmed
                        status = 'confirmed'
                else:
                    # Past appointment (within last 60 days)
                    days_ago = random.randint(1, 60)
                    appointment_date = today - datetime.timedelta(days=days_ago)
                    if random.random() < 0.1:  # 10% of past appointments were cancelled
                        status = 'cancelled'
                    elif random.random() < 0.05:  # 5% of past appointments were no-shows
                        status = 'no_show'
                    else:  # 85% were completed
                        status = 'completed'
                
                # Set time between 8:00 and 16:00
                hour = random.randint(8, 16)
                minute = random.choice([0, 15, 30, 45])
                appointment_datetime = datetime.datetime.combine(
                    appointment_date, 
                    datetime.time(hour, minute)
                )
                
                # Set timezone-aware datetime
                appointment_datetime = timezone.make_aware(appointment_datetime)
                
                # Appointment reasons
                reasons = [
                    'Consultation initiale',
                    'Suivi régulier',
                    'Évaluation de la progression',
                    'Ajustement du plan de traitement',
                    'Session de kinésithérapie',
                    'Session d\'orthophonie',
                    'Évaluation nutritionnelle',
                    'Bilan orthopédique',
                    'Suivi neurologique',
                    'Consultation post-hospitalisation'
                ]
                
                appointment = Appointment.objects.create(
                    patient=patient,
                    doctor=doctor,
                    facility=facility,
                    appointment_date=appointment_datetime,
                    reason=random.choice(reasons),
                    status=status,
                    notes=f"Notes de rendez-vous pour {patient.first_name}" if random.random() < 0.5 else ""
                )
                
        self.stdout.write(f'Created appointments for {len(patients)} patients')
    
    def create_rehabilitation_plans(self, patients, doctors):
        """Create rehabilitation plans for patients"""
        today = timezone.now().date()
        
        # Only create plans for about 70% of patients (not all need rehabilitation)
        for patient in random.sample(patients, k=int(len(patients) * 0.7)):
            # Get a doctor
            doctor = random.choice(doctors)
            
            # Create a plan with start date between 2 weeks and 6 months ago
            days_ago = random.randint(14, 180)
            start_date = today - datetime.timedelta(days=days_ago)
            
            # End date is either None (ongoing) or up to 1 year after start date
            if random.random() < 0.7:  # 70% of plans are still active
                end_date = None
                status = 'active'
            else:
                duration_days = random.randint(30, 365)
                end_date = start_date + datetime.timedelta(days=duration_days)
                if end_date < today:  # If end date is in the past
                    status = 'completed'
                else:
                    status = 'active'
            
            # Get the most recent medical record for this patient to use the diagnosis
            latest_record = MedicalRecord.objects.filter(patient=patient).order_by('-date').first()
            diagnosis = latest_record.diagnosis if latest_record else "Condition nécessitant réhabilitation"
            
            # Rehabilitation goals based on diagnosis
            goals_by_diagnosis = {
                'Paralysie cérébrale': "1. Améliorer la mobilité des membres\n2. Renforcer les muscles du tronc\n3. Faciliter les activités quotidiennes\n4. Améliorer la posture assise",
                'Retard de développement': "1. Stimuler le développement cognitif\n2. Améliorer la coordination\n3. Développer la motricité fine\n4. Favoriser la communication",
                'Malnutrition': "1. Retrouver un poids optimal\n2. Récupérer la force musculaire\n3. Améliorer l'état nutritionnel\n4. Optimiser le développement",
                'Séquelles de paludisme cérébral': "1. Récupérer les fonctions motrices\n2. Améliorer la coordination\n3. Restaurer les fonctions cognitives\n4. Gérer les séquelles neurologiques",
                'Handicap moteur': "1. Augmenter l'amplitude des mouvements\n2. Renforcer les capacités motrices\n3. Faciliter la mobilité quotidienne\n4. Prévenir les complications orthopédiques",
            }
            
            goals = goals_by_diagnosis.get(diagnosis, "1. Objectifs personnalisés à définir avec l'équipe de réadaptation")
            
            # Create rehabilitation plan
            rehab_plan = RehabilitationPlan.objects.create(
                patient=patient,
                prescribing_doctor=doctor,
                start_date=start_date,
                end_date=end_date,
                diagnosis=diagnosis,
                goals=goals,
                status=status
            )
            
            # Create rehabilitation sessions
            self.create_rehabilitation_sessions(rehab_plan, doctor)
            
        self.stdout.write(f'Created rehabilitation plans for patients')
    
    def create_rehabilitation_sessions(self, rehab_plan, doctor):
        """Create rehabilitation sessions for a rehabilitation plan"""
        # Between 5-15 sessions per plan
        num_sessions = random.randint(5, 15)
        start_date = rehab_plan.start_date
        today = timezone.now().date()
        
        session_types = [
            'Kinésithérapie',
            'Physiothérapie',
            'Ergothérapie',
            'Orthophonie',
            'Stimulation cognitive',
            'Rééducation fonctionnelle',
            'Hydrothérapie',
            'Thérapie psychomotrice'
        ]
        
        for i in range(num_sessions):
            # Session date: evenly distributed between start date and today (or end date if exists)
            end_date = rehab_plan.end_date if rehab_plan.end_date else today
            total_days = (end_date - start_date).days
            if total_days <= 0:
                # If plan was just created, schedule sessions in the future
                session_date = start_date + datetime.timedelta(days=i*7)  # Weekly sessions
            else:
                day_offset = int(i * total_days / num_sessions)
                session_date = start_date + datetime.timedelta(days=day_offset)
            
            # Set time between 8:00 and 16:00
            hour = random.randint(8, 16)
            minute = random.choice([0, 15, 30, 45])
            session_datetime = datetime.datetime.combine(
                session_date, 
                datetime.time(hour, minute)
            )
            
            # Set timezone-aware datetime
            session_datetime = timezone.make_aware(session_datetime)
            
            # Determine status based on date
            if session_date > today:
                status = 'planned'
            else:
                if random.random() < 0.1:  # 10% chance of cancelled or missed
                    status = random.choice(['cancelled', 'missed'])
                else:
                    status = 'completed'
            
            # Notes for completed sessions
            notes = ""
            if status == 'completed':
                progress_notes = [
                    "Le patient montre une amélioration notable dans la mobilité.",
                    "Progrès satisfaisants. Continuer le plan actuel.",
                    "Légère amélioration observée. Ajustement du plan recommandé.",
                    "Bonne participation à la séance. Exercices à domicile expliqués.",
                    "Difficulté à réaliser certains exercices. Plan à adapter.",
                    "Progrès constants. Patient très motivé.",
                    "Amélioration de la coordination. Continuer les exercices."
                ]
                notes = random.choice(progress_notes)
            
            facility = doctor.facility
            
            RehabilitationSession.objects.create(
                rehabilitation_plan=rehab_plan,
                therapist=doctor,
                facility=facility,
                session_date=session_datetime,
                session_type=random.choice(session_types),
                duration_minutes=random.choice([30, 45, 60, 90]),
                notes=notes,
                status=status
            )
    
    def create_vouchers(self, patients, doctors, facilities):
        """Create vouchers for patients"""
        today = timezone.now().date()
        
        # Services that could require vouchers
        service_types = [
            'Consultation spécialisée',
            'Kinésithérapie',
            'Séance de réhabilitation',
            'Orthophonie',
            'Appareillage orthopédique',
            'Examen complémentaire',
            'Prise en charge psychologique',
            'Aide technique'
        ]
        
        # Create 1-3 vouchers for 80% of patients
        for patient in random.sample(patients, k=int(len(patients) * 0.8)):
            num_vouchers = random.randint(1, 3)
            
            for i in range(num_vouchers):
                issuing_doctor = random.choice(doctors)
                issuing_facility = issuing_doctor.facility or random.choice(facilities)
                
                # Target facility should be different from issuing facility
                other_facilities = [f for f in facilities if f != issuing_facility]
                if other_facilities:
                    target_facility = random.choice(other_facilities)
                else:
                    target_facility = issuing_facility
                
                # Issue date between 1-90 days ago
                days_ago = random.randint(1, 90)
                issue_date = today - datetime.timedelta(days=days_ago)
                
                # Expiry date between 30-180 days after issue date
                validity_days = random.randint(30, 180)
                expiry_date = issue_date + datetime.timedelta(days=validity_days)
                
                # Status based on dates
                if expiry_date < today:
                    status = 'expired'
                else:
                    # Active vouchers:
                    # 50% issued, 30% validated, 20% used
                    rand = random.random()
                    if rand < 0.5:
                        status = 'issued'
                        validated_by = None
                        validated_date = None
                    elif rand < 0.8:
                        status = 'validated'
                        validated_by = random.choice(doctors)
                        days_after_issue = random.randint(1, min(10, (today - issue_date).days))
                        validated_date = timezone.make_aware(datetime.datetime.combine(
                            issue_date + datetime.timedelta(days=days_after_issue),
                            datetime.time(random.randint(8, 17), random.choice([0, 15, 30, 45]))
                        ))
                    else:
                        status = 'used'
                        validated_by = random.choice(doctors)
                        days_after_issue = random.randint(1, min(20, (today - issue_date).days))
                        validated_date = timezone.make_aware(datetime.datetime.combine(
                            issue_date + datetime.timedelta(days=days_after_issue),
                            datetime.time(random.randint(8, 17), random.choice([0, 15, 30, 45]))
                        ))
                
                service_type = random.choice(service_types)
                description = f"Bon pour {service_type} à {target_facility.name}"
                
                voucher = Voucher.objects.create(
                    patient=patient,
                    issuing_doctor=issuing_doctor,
                    issuing_facility=issuing_facility,
                    target_facility=target_facility,
                    service_type=service_type,
                    description=description,
                    issue_date=issue_date,
                    expiry_date=expiry_date,
                    status=status,
                    validated_by=validated_by,
                    validated_date=validated_date
                )
                
        self.stdout.write(f'Created vouchers for patients') 