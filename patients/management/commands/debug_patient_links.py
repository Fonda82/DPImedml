from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import UserProfile
from patients.models import Patient
from appointments.models import Appointment
from vouchers.models import Voucher
from rehabilitation.models import RehabilitationPlan, RehabilitationSession
from django.utils import timezone

class Command(BaseCommand):
    help = 'Debug and fix patient user links to ensure menus show data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔍 Debugging patient user links...'))
        
        try:
            # Check if patient user exists
            try:
                patient_user = User.objects.get(username='patient')
                self.stdout.write(f"✅ Patient user found: {patient_user.username}")
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR('❌ Patient user not found'))
                return
            
            # Check if patient profile exists
            try:
                patient_profile = UserProfile.objects.get(user=patient_user)
                self.stdout.write(f"✅ Patient profile found: {patient_profile.user_type}")
            except UserProfile.DoesNotExist:
                self.stdout.write(self.style.ERROR('❌ Patient profile not found'))
                return
            
            # Check if patient record exists
            try:
                patient_record = Patient.objects.get(user=patient_user)
                self.stdout.write(f"✅ Patient record found: {patient_record.first_name} {patient_record.last_name}")
                patient_id = patient_record.id
            except Patient.DoesNotExist:
                self.stdout.write(self.style.WARNING('⚠️  Patient record not linked to user'))
                # Find Modibo Kané with ID P-A4CCB9D2
                modibo_patients = Patient.objects.filter(patient_id='P-A4CCB9D2')
                if modibo_patients.exists():
                    patient_record = modibo_patients.first()
                    patient_record.user = patient_user
                    patient_record.save()
                    self.stdout.write(f"🔗 Linked user to Patient: {patient_record.first_name} {patient_record.last_name} (ID: {patient_record.patient_id})")
                    patient_id = patient_record.id
                else:
                    # Fallback: find any Modibo Kané
                    modibo_fallback = Patient.objects.filter(first_name='Modibo', last_name__icontains='Kané')
                    if modibo_fallback.exists():
                        patient_record = modibo_fallback.first()
                        patient_record.user = patient_user
                        patient_record.save()
                        self.stdout.write(f"🔗 Linked user to Patient: {patient_record.first_name} {patient_record.last_name} (ID: {patient_record.patient_id})")
                        patient_id = patient_record.id
                    else:
                        self.stdout.write(self.style.ERROR('❌ No Modibo Kané patients found to link'))
                        # Show available patients
                        all_patients = Patient.objects.all()[:10]
                        self.stdout.write('Available patients:')
                        for p in all_patients:
                            self.stdout.write(f"  - {p.first_name} {p.last_name} (ID: {p.patient_id})")
                        return
            
            # Check appointments
            appointments = Appointment.objects.filter(patient=patient_record)
            self.stdout.write(f"📅 Found {appointments.count()} appointments for patient")
            
            # Check vouchers
            vouchers = Voucher.objects.filter(patient=patient_record)
            self.stdout.write(f"🎫 Found {vouchers.count()} vouchers for patient")
            
            # Check rehabilitation plans
            rehab_plans = RehabilitationPlan.objects.filter(patient=patient_record)
            self.stdout.write(f"🏃‍♂️ Found {rehab_plans.count()} rehabilitation plans for patient")
            
            # Test the views logic
            self.stdout.write('\n🧪 Testing view filters...')
            
            # Test appointments view logic
            try:
                test_patient = Patient.objects.get(user=patient_user)
                test_appointments = Appointment.objects.filter(patient=test_patient)
                self.stdout.write(f"📅 Appointments view would show: {test_appointments.count()} appointments")
            except Patient.DoesNotExist:
                self.stdout.write(f"❌ Appointments view would show: 0 appointments (Patient.DoesNotExist)")
            
            # Test vouchers view logic
            try:
                test_patient = Patient.objects.get(user=patient_user)
                test_vouchers = Voucher.objects.filter(patient=test_patient)
                self.stdout.write(f"🎫 Vouchers view would show: {test_vouchers.count()} vouchers")
            except Patient.DoesNotExist:
                self.stdout.write(f"❌ Vouchers view would show: 0 vouchers (Patient.DoesNotExist)")
            
            # Test exercises view logic
            try:
                test_patient = Patient.objects.get(user=patient_user)
                active_plan = RehabilitationPlan.objects.filter(
                    patient=test_patient,
                    status='active'
                ).first()
                if active_plan:
                    sessions = RehabilitationSession.objects.filter(
                        rehabilitation_plan=active_plan
                    ).exclude(notes__isnull=True).exclude(notes__exact='')
                    self.stdout.write(f"🏃‍♂️ Exercises view would show: {sessions.count()} exercise sessions")
                else:
                    self.stdout.write(f"🏃‍♂️ Exercises view would show: 0 exercises (No active plan)")
            except Patient.DoesNotExist:
                self.stdout.write(f"❌ Exercises view would show: 0 exercises (Patient.DoesNotExist)")
            
            # Show URLs for testing
            self.stdout.write('\n🔗 Test these URLs:')
            self.stdout.write(f"Dashboard: /dashboard/")
            self.stdout.write(f"Appointments: /appointments/")
            self.stdout.write(f"Exercises: /rehabilitation/patient-exercises/")
            self.stdout.write(f"Vouchers: /vouchers/")
            self.stdout.write(f"Medical Profile: /patients/medical_profile/{patient_id}/")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error during diagnosis: {str(e)}'))
            
        self.stdout.write(self.style.SUCCESS('✅ Patient link diagnosis completed!')) 