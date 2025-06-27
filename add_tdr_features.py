 h#!/usr/bin/env python
import os
import sys
import django
import datetime
import random

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dpimedml.settings')
django.setup()

from django.utils import timezone
from django.contrib.auth.models import User
from accounts.models import UserProfile
from patients.models import Patient, Hospitalization, HospitalizationProgressNote
from facilities.models import Facility, InterFacilityCommunication
from referrals.models import Referral, ReferralResponse

def create_tdr_demo_data():
    print("🇲🇱 Creating TDR Demo Data for Dashboards...")
    
    # Get existing data
    facilities = list(Facility.objects.all())
    doctors = list(UserProfile.objects.filter(user_type='doctor'))
    patients = list(Patient.objects.all())
    
    if not facilities or not doctors or not patients:
        print("❌ No base data found. Run enhanced_mali_demo_data first.")
        return
    
    print(f"📊 Found: {len(facilities)} facilities, {len(doctors)} doctors, {len(patients)} patients")
    
    # 1. Create hospitalizations
    print("🏥 Creating TDR Hospitalization Data...")
    hospitalizations = create_hospitalizations(patients, doctors, facilities)
    create_hospitalization_progress(hospitalizations, doctors)
    
    # 2. Create referrals
    print("🔄 Creating TDR Referral System...")
    referrals = create_referrals(patients, doctors, facilities)
    create_referral_responses(referrals, doctors)
    
    # 3. Create inter-facility communications
    print("💬 Creating Inter-facility Communications...")
    create_inter_facility_communications(facilities, doctors)
    
    # Display statistics
    print("📊 TDR Dashboard Statistics Summary:")
    display_dashboard_stats()
    
    print("🎉 TDR Demo Data created successfully!")
    print("✅ All TDR features integrated with dashboard statistics")

def create_hospitalizations(patients, doctors, facilities):
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
    
    print(f"🏥 Created {len(hospitalizations)} hospitalizations")
    return hospitalizations

def create_hospitalization_progress(hospitalizations, doctors):
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
    
    print(f"📝 Created {progress_notes} progress notes")

def create_referrals(patients, doctors, facilities):
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
            status=random.choice(['pending', 'accepted', 'completed', 'pending', 'accepted']),
            referral_date=referral_date
        )
        referrals.append(referral)
    
    print(f"🔄 Created {len(referrals)} inter-facility referrals")
    return referrals

def create_referral_responses(referrals, doctors):
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
    
    print(f"📨 Created {responses} referral responses")

def create_inter_facility_communications(facilities, doctors):
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
    
    print(f"💬 Created {len(communications)} inter-facility communications")

def display_dashboard_stats():
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
        
        print('📊 TDR Dashboard Statistics:')
        print(f'  🏥 Hospitalizations: {total_hospitalizations} total, {current_hospitalizations} current')
        print(f'  🔄 Referrals: {total_referrals} total, {pending_referrals} pending, {accepted_referrals} accepted')
        print(f'  💬 Communications: {total_communications} total, {recent_communications} this week')
        
    except Exception as e:
        print(f'⚠️ Could not display stats: {str(e)}')

if __name__ == '__main__':
    create_tdr_demo_data() 