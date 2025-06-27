from django.core.management.base import BaseCommand
from patients.models import Patient

class Command(BaseCommand):
    help = 'Test patient relationships used in detail template'

    def handle(self, *args, **options):
        # Test Modibo Kané specifically
        try:
            modibo = Patient.objects.get(first_name='Modibo', last_name='Kané')
            self.stdout.write(f'🔍 Testing relationships for {modibo.first_name} {modibo.last_name} (ID: {modibo.id})')
            
            # Test rehabilitation_plans relationship
            try:
                rehab_plans = modibo.rehabilitation_plans.all()
                self.stdout.write(f'✅ patient.rehabilitation_plans.all(): {rehab_plans.count()} plans')
                for plan in rehab_plans:
                    self.stdout.write(f'   - {plan.diagnosis} ({plan.status})')
            except Exception as e:
                self.stdout.write(f'❌ patient.rehabilitation_plans.all(): ERROR - {e}')

            # Test vouchers relationship  
            try:
                vouchers = modibo.vouchers.all()
                self.stdout.write(f'✅ patient.vouchers.all(): {vouchers.count()} vouchers')
                for voucher in vouchers[:3]:
                    self.stdout.write(f'   - {voucher.service_type} ({voucher.status})')
            except Exception as e:
                self.stdout.write(f'❌ patient.vouchers.all(): ERROR - {e}')

            # Test appointments relationship
            try:
                appointments = modibo.appointments.all()
                self.stdout.write(f'✅ patient.appointments.all(): {appointments.count()} appointments')
                for appt in appointments[:3]:
                    date_str = appt.appointment_date.strftime('%d/%m/%Y') if appt.appointment_date else 'N/A'
                    self.stdout.write(f'   - {appt.reason or "Consultation"} on {date_str}')
            except Exception as e:
                self.stdout.write(f'❌ patient.appointments.all(): ERROR - {e}')
                
        except Patient.DoesNotExist:
            self.stdout.write('❌ Modibo Kané not found') 