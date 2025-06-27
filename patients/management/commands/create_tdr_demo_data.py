from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
import random

from patients.models import Patient, Hospitalization, HospitalizationProgressNote, DischargeReport
from referrals.models import Referral, ReferralResponse, ReferralFollowUp
from facilities.models import Facility, InterFacilityCommunication, FacilityCapability
from accounts.models import UserProfile


class Command(BaseCommand):
    help = 'Create demo data for TDR features: hospitalizations, referrals, and inter-facility communication'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating TDR demo data...'))
        
        # Get existing data
        patients = list(Patient.objects.all()[:10])
        facilities = list(Facility.objects.all())
        doctors = list(UserProfile.objects.filter(user_type='doctor'))
        
        if not patients:
            self.stdout.write(self.style.ERROR('No patients found. Run create_modibo_demo_data first.'))
            return
            
        if not facilities:
            self.stdout.write(self.style.ERROR('No facilities found. Please create facilities first.'))
            return
            
        if not doctors:
            self.stdout.write(self.style.ERROR('No doctors found. Please create doctor profiles first.'))
            return

        # Create hospitalization demo data
        self.create_hospitalizations(patients, doctors)
        
        # Create referral demo data
        self.create_referrals(patients, facilities, doctors)
        
        # Create inter-facility communication demo data
        self.create_facility_communications(facilities, doctors)
        
        # Create facility capabilities
        self.create_facility_capabilities(facilities)
        
        self.stdout.write(self.style.SUCCESS('✅ TDR demo data created successfully!'))

    def create_hospitalizations(self, patients, doctors):
        """Create sample hospitalizations"""
        self.stdout.write('Creating hospitalizations...')
        
        # Create 5-8 hospitalizations
        for i in range(random.randint(5, 8)):
            patient = random.choice(patients)
            doctor = random.choice(doctors)
            
            # Admission date (last 30 days)
            admission_date = timezone.now() - timedelta(days=random.randint(0, 30))
            
            # Some are discharged, some are still admitted
            status = random.choice(['admitted', 'admitted', 'discharged', 'discharged', 'transferred'])
            discharge_date = None
            
            if status == 'discharged':
                discharge_date = admission_date + timedelta(days=random.randint(1, 14))
            elif status == 'transferred':
                discharge_date = admission_date + timedelta(days=random.randint(1, 7))
            
            hospitalization = Hospitalization.objects.create(
                patient=patient,
                admission_date=admission_date,
                discharge_date=discharge_date,
                admitting_doctor=doctor,
                attending_doctor=doctor,
                admission_reason=random.choice([
                    'Complications post-chirurgicales',
                    'Crise d\'épilepsie sévère',
                    'Infection respiratoire',
                    'Réévaluation du plan de traitement',
                    'Thérapie intensive de réadaptation',
                    'Surveillance post-opératoire'
                ]),
                admission_diagnosis=random.choice([
                    'Paralysie cérébrale avec complications',
                    'Épilepsie réfractaire',
                    'Pneumonie associée aux soins',
                    'Retard de développement sévère',
                    'Malnutrition sévère',
                    'Hydrocéphalie'
                ]),
                room_number=random.choice(['pediatrie_A', 'pediatrie_B', 'readaptation', 'soins_intensifs']),
                bed_number=f"{random.randint(1, 20):02d}",
                status=status
            )
            
            # Add progress notes for active hospitalizations
            if status == 'admitted':
                self.create_progress_notes(hospitalization, doctor)
            
            # Add discharge report for completed stays
            if status in ['discharged', 'transferred']:
                self.create_discharge_report(hospitalization, doctor)

    def create_progress_notes(self, hospitalization, doctor):
        """Create daily progress notes"""
        start_date = hospitalization.admission_date.date()
        days_admitted = (timezone.now().date() - start_date).days
        
        for day in range(min(days_admitted, 7)):  # Last 7 days max
            note_date = start_date + timedelta(days=day)
            shift = random.choice(['morning', 'afternoon', 'night'])
            
            HospitalizationProgressNote.objects.create(
                hospitalization=hospitalization,
                date=note_date,
                time=timezone.now().time(),
                shift=shift,
                author=doctor,
                progress_note=random.choice([
                    'Patient stable, amélioration notable de la mobilité',
                    'Séance de kinésithérapie bien tolérée, pas de complications',
                    'Appétit en amélioration, interaction sociale positive',
                    'Légers progrès dans les exercices de motricité fine',
                    'État général satisfaisant, famille présente et rassurée'
                ]),
                treatment_administered=random.choice([
                    'Kinésithérapie 2x/jour, médicaments anti-spastiques',
                    'Ergothérapie, suppléments nutritionnels',
                    'Séances d\'orthophonie, exercices respiratoires',
                    'Thérapie occupationnelle, soutien psychologique'
                ]),
                temperature=round(random.uniform(36.5, 37.8), 1),
                heart_rate=random.randint(80, 120),
                respiratory_rate=random.randint(16, 24),
                weight=round(random.uniform(8.0, 25.0), 1),
                family_visit=random.choice([True, False]),
                family_notes='Famille très impliquée dans les soins' if random.choice([True, False]) else ''
            )

    def create_discharge_report(self, hospitalization, doctor):
        """Create discharge report"""
        DischargeReport.objects.create(
            hospitalization=hospitalization,
            discharge_type=random.choice(['home', 'rehabilitation', 'transfer']),
            discharge_condition=random.choice(['improved', 'stable', 'cured']),
            final_diagnosis=hospitalization.admission_diagnosis + ' - Traité avec succès',
            treatment_summary=random.choice([
                'Traitement intensif de réadaptation avec kinésithérapie quotidienne',
                'Prise en charge multidisciplinaire: médecine, kinésithérapie, orthophonie',
                'Stabilisation nutritionnelle et thérapie motrice adaptée',
                'Programme complet de réadaptation pédiatrique'
            ]),
            follow_up_instructions=random.choice([
                'Suivi hebdomadaire en consultation externe, continuer la kinésithérapie',
                'RDV mensuel, exercices à domicile selon protocole fourni',
                'Surveillance régulière, poursuite du programme de réadaptation',
                'Contrôles trimestriels, maintien des acquis thérapeutiques'
            ]),
            medications_at_discharge='Selon ordonnance remise à la famille',
            next_appointment_date=timezone.now().date() + timedelta(days=random.randint(7, 30)),
            family_education_provided=True,
            family_education_notes='Formation de la famille aux exercices quotidiens',
            rehabilitation_goals_achieved=random.choice([
                'Amélioration de 40% de la motricité globale',
                'Autonomie alimentaire retrouvée',
                'Communication verbale améliorée',
                'Mobilité en fauteuil roulant maîtrisée'
            ]),
            home_exercise_program='Programme d\'exercices quotidiens remis à la famille',
            discharge_prepared_by=doctor
        )

    def create_referrals(self, patients, facilities, doctors):
        """Create sample referrals between facilities"""
        self.stdout.write('Creating referrals...')
        
        if len(facilities) < 2:
            self.stdout.write('Need at least 2 facilities for referrals')
            return
        
        # Create 8-12 referrals
        for i in range(random.randint(8, 12)):
            patient = random.choice(patients)
            referring_doctor = random.choice(doctors)
            
            # Pick different facilities
            referring_facility = random.choice(facilities)
            receiving_facility = random.choice([f for f in facilities if f != referring_facility])
            
            referral = Referral.objects.create(
                patient=patient,
                referring_facility=referring_facility,
                receiving_facility=receiving_facility,
                referring_doctor=referring_doctor,
                referral_type=random.choice(['consultation', 'rehabilitation', 'diagnostic', 'surgery']),
                priority=random.choice(['normal', 'high', 'urgent']),
                specialty_requested=random.choice([
                    'Neurologie pédiatrique',
                    'Orthopédie',
                    'Kinésithérapie spécialisée',
                    'Chirurgie pédiatrique',
                    'Radiologie',
                    'Psychologie'
                ]),
                reason_for_referral=random.choice([
                    'Évaluation spécialisée pour spasticité sévère',
                    'Bilan approfondi des troubles moteurs',
                    'Consultation pré-opératoire en neurochirurgie',
                    'Rééducation intensive post-trauma',
                    'Évaluation cognitive et comportementale',
                    'Imagerie spécialisée (IRM cérébrale)'
                ]),
                clinical_summary=f'Patient de {patient.date_of_birth.year if patient.date_of_birth else "X"} ans avec handicap moteur nécessitant évaluation spécialisée',
                current_diagnosis=random.choice([
                    'Paralysie cérébrale spastique',
                    'Retard psychomoteur',
                    'Épilepsie pharmacorésistante',
                    'Malformation congénitale',
                    'Traumatisme crânien'
                ]),
                status=random.choice(['pending', 'accepted', 'completed', 'pending']),
                preferred_date=timezone.now().date() + timedelta(days=random.randint(7, 30))
            )
            
            # Add response for some referrals
            if referral.status in ['accepted', 'completed']:
                self.create_referral_response(referral, doctors)

    def create_referral_response(self, referral, doctors):
        """Create referral response"""
        responding_doctor = random.choice(doctors)
        
        ReferralResponse.objects.create(
            referral=referral,
            response_type='acceptance',
            responding_doctor=responding_doctor,
            response_message=random.choice([
                'Référence acceptée. RDV programmé selon disponibilités.',
                'Patient pris en charge. Évaluation prévue la semaine prochaine.',
                'Acceptation confirmée. Préparation du dossier en cours.',
                'RDV fixé. Documents complémentaires demandés.'
            ]),
            proposed_appointment_date=timezone.now() + timedelta(days=random.randint(5, 15)),
            assigned_doctor=responding_doctor,
            service_location='Consultation externe',
            estimated_cost=random.randint(0, 50000),  # CFA
            expected_duration='2-3 heures',
            follow_up_required=True,
            follow_up_instructions='Suivi recommandé après évaluation initiale'
        )

    def create_facility_communications(self, facilities, doctors):
        """Create inter-facility communications"""
        self.stdout.write('Creating inter-facility communications...')
        
        if len(facilities) < 2:
            return
        
        # Create 5-8 communications
        for i in range(random.randint(5, 8)):
            from_facility = random.choice(facilities)
            to_facility = random.choice([f for f in facilities if f != from_facility])
            sender = random.choice(doctors)
            
            InterFacilityCommunication.objects.create(
                from_facility=from_facility,
                to_facility=to_facility,
                communication_type=random.choice([
                    'referral', 'voucher_validation', 'information_request', 'resource_sharing'
                ]),
                subject=random.choice([
                    'Demande de transfert patient urgent',
                    'Validation bon de service n°12345',
                    'Partage protocole rééducation',
                    'Information nouveau programme',
                    'Coordination prise en charge'
                ]),
                message=random.choice([
                    'Demande de validation urgente pour prise en charge spécialisée',
                    'Merci de confirmer la disponibilité pour accueil patient',
                    'Nouveau protocole de rééducation disponible, formation proposée',
                    'Information sur les nouvelles modalités de prise en charge',
                    'Coordination nécessaire pour suivi patient complexe'
                ]),
                sent_by=sender,
                status=random.choice(['sent', 'delivered', 'read']),
                is_urgent=random.choice([True, False]),
                requires_response=random.choice([True, False])
            )

    def create_facility_capabilities(self, facilities):
        """Create facility capabilities"""
        self.stdout.write('Creating facility capabilities...')
        
        capabilities = [
            ('pediatrics', 'Pédiatrie'),
            ('rehabilitation', 'Réadaptation'),
            ('orthopedics', 'Orthopédie'),
            ('neurology', 'Neurologie'),
            ('physiotherapy', 'Kinésithérapie'),
            ('occupational_therapy', 'Ergothérapie'),
            ('speech_therapy', 'Orthophonie')
        ]
        
        for facility in facilities:
            # Each facility gets 3-5 random capabilities
            selected_caps = random.sample(capabilities, random.randint(3, 5))
            
            for cap_code, cap_name in selected_caps:
                FacilityCapability.objects.get_or_create(
                    facility=facility,
                    name=cap_code,
                    defaults={
                        'capability_type': 'specialty',
                        'description': f'Service de {cap_name.lower()} spécialisé',
                        'is_available': True,
                        'capacity_level': random.choice(['basic', 'intermediate', 'advanced']),
                        'available_days': 'Lundi-Vendredi',
                        'available_hours': '08:00-17:00',
                        'max_patients_per_day': random.randint(5, 15),
                        'current_wait_time_days': random.randint(1, 14)
                    }
                ) 