from django.core.management.base import BaseCommand
from patients.models import Patient
from rehabilitation.models import RehabilitationPlan
from vouchers.models import Voucher

class Command(BaseCommand):
    help = 'Check which patients have rehabilitation plans and vouchers'

    def handle(self, *args, **options):
        self.stdout.write('🔍 Checking patient data...')
        
        # Check all patients and their data
        patients = Patient.objects.all()
        
        for patient in patients:
            rehab_count = patient.rehabilitation_plans.count()
            voucher_count = patient.vouchers.count()
            appointment_count = patient.appointments.count()
            
            if rehab_count > 0 or voucher_count > 0 or appointment_count > 0:
                self.stdout.write(
                    f"Patient {patient.id}: {patient.first_name} {patient.last_name} "
                    f"(ID: {patient.patient_id}) - "
                    f"Rehab: {rehab_count}, Vouchers: {voucher_count}, Appointments: {appointment_count}"
                )
        
        # Show specifically Modibo Kané
        modibo = Patient.objects.filter(first_name='Modibo', last_name='Kané').first()
        if modibo:
            self.stdout.write(f"\n✅ Modibo Kané found: Patient ID {modibo.id}")
            self.stdout.write(f"   Database ID: {modibo.id}")
            self.stdout.write(f"   Patient ID: {modibo.patient_id}")
            self.stdout.write(f"   Rehab plans: {modibo.rehabilitation_plans.count()}")
            self.stdout.write(f"   Vouchers: {modibo.vouchers.count()}")
            self.stdout.write(f"   Appointments: {modibo.appointments.count()}")
        else:
            self.stdout.write("❌ Modibo Kané not found") 