from django.core.management.base import BaseCommand
from patients.models import Patient
from django.db.models import Count

class Command(BaseCommand):
    help = 'Test which patients the doctor dashboard will show'

    def handle(self, *args, **options):
        self.stdout.write('🔍 Testing doctor dashboard patient selection...')
        
        # Simulate the exact query from the updated doctor dashboard
        patients_with_rehab = Patient.objects.filter(
            rehabilitation_plans__isnull=False
        ).distinct().annotate(
            rehab_count=Count('rehabilitation_plans'),
            voucher_count=Count('vouchers')
        ).order_by('-rehab_count', '-voucher_count')[:3]
        
        self.stdout.write('Top 3 patients with rehabilitation plans:')
        for i, patient in enumerate(patients_with_rehab, 1):
            self.stdout.write(
                f"  {i}. {patient.first_name} {patient.last_name} "
                f"(ID: {patient.patient_id}) - "
                f"Rehab: {patient.rehab_count}, Vouchers: {patient.voucher_count}"
            )
        
        # Fill remaining slots
        remaining_slots = 5 - patients_with_rehab.count()
        if remaining_slots > 0:
            other_patients = Patient.objects.filter(
                medicalrecord__isnull=False
            ).exclude(
                id__in=patients_with_rehab.values_list('id', flat=True)
            ).distinct()[:remaining_slots]
            
            self.stdout.write(f'\nRemaining {remaining_slots} patients with medical records:')
            for i, patient in enumerate(other_patients, 1):
                self.stdout.write(f"  {i}. {patient.first_name} {patient.last_name} (ID: {patient.patient_id})")
        
        # Final list that would appear in dashboard
        final_list = list(patients_with_rehab) + (list(other_patients) if remaining_slots > 0 else [])
        
        self.stdout.write('\n✅ Final patient list for doctor dashboard:')
        for i, patient in enumerate(final_list, 1):
            self.stdout.write(f"  {i}. {patient.first_name} {patient.last_name} (ID: {patient.patient_id})") 