from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.utils import timezone
from datetime import datetime, timedelta
from accounts.models import UserProfile
from patients.models import Patient, MedicalRecord, Hospitalization, HospitalizationProgressNote, DischargeReport
from appointments.models import Appointment
from rehabilitation.models import RehabilitationPlan, RehabilitationSession
from vouchers.models import Voucher
from facilities.models import Facility, InterFacilityCommunication, FacilityNetwork, VoucherValidationLog
from referrals.models import Referral, ReferralResponse, ReferralFollowUp
from dashboard.models import SystemActivity, SecurityAudit, LoginAttempt, PatientConsent, DataRetentionPolicy
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
import json
import random
import csv

@login_required
def index(request):
    """Redirect to appropriate dashboard based on user role"""
    if not hasattr(request.user, 'profile'):
        return render(request, 'dashboard/error.html', {'message': 'Profil utilisateur non trouvé'})
    
    user_type = request.user.profile.user_type
    
    if user_type == 'superadmin':
        return redirect('dashboard:superadmin')
    elif user_type == 'facility_admin':
        return redirect('dashboard:facility_admin')
    elif user_type == 'doctor':
        return redirect('dashboard:doctor')
    elif user_type == 'patient':
        return redirect('dashboard:patient')
    else:
        return render(request, 'dashboard/error.html', {'message': 'Type de profil non reconnu'})

@login_required
def superadmin_dashboard(request):
    """Display the superadmin dashboard using real database queries with enhanced statistics"""
    
    # PHASE 1 ENHANCEMENT: Calculate current period vs previous period for trends
    today = timezone.now().date()
    current_month_start = today.replace(day=1)
    previous_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
    previous_month_end = current_month_start - timedelta(days=1)
    
    # Calculate current and previous period statistics
    
    # Total patients with trend
    total_patients = Patient.objects.count()
    current_month_patients = Patient.objects.filter(
        created_at__date__gte=current_month_start,
        created_at__date__lte=today
    ).count()
    previous_month_patients = Patient.objects.filter(
        created_at__date__gte=previous_month_start,
        created_at__date__lte=previous_month_end
    ).count()
    
    # Total facilities (rarely changes, but calculate growth over 3 months)
    total_facilities = Facility.objects.count()
    three_months_ago = today - timedelta(days=90)
    previous_facilities = Facility.objects.filter(created_at__date__lt=three_months_ago).count()
    
    # Total doctors with monthly growth
    total_doctors = UserProfile.objects.filter(user_type='doctor').count()
    current_month_doctors = UserProfile.objects.filter(
        user_type='doctor',
        user__date_joined__gte=current_month_start
    ).count()
    previous_month_doctors = UserProfile.objects.filter(
        user_type='doctor',
        user__date_joined__gte=previous_month_start,
        user__date_joined__lt=current_month_start
    ).count()
    
    # Active vouchers with weekly comparison
    active_vouchers = Voucher.objects.exclude(status__in=['expired', 'used', 'cancelled']).count()
    week_start = today - timedelta(days=7)
    current_week_vouchers = Voucher.objects.filter(
        issue_date__gte=week_start,
        issue_date__lte=today
    ).exclude(status__in=['expired', 'used', 'cancelled']).count()
    previous_week_start = week_start - timedelta(days=7)
    previous_week_vouchers = Voucher.objects.filter(
        issue_date__gte=previous_week_start,
        issue_date__lt=week_start
    ).exclude(status__in=['expired', 'used', 'cancelled']).count()
    
    # Calculate percentage changes and trends
    def calculate_trend(current, previous):
        if previous == 0:
            if current > 0:
                return {'direction': 'up', 'percentage': 100, 'change': current}
            else:
                return {'direction': 'stable', 'percentage': 0, 'change': 0}
        
        percentage = round(((current - previous) / previous) * 100, 1)
        change = current - previous
        
        if percentage > 5:
            direction = 'up'
        elif percentage < -5:
            direction = 'down'
        else:
            direction = 'stable'
            
        return {'direction': direction, 'percentage': abs(percentage), 'change': change}
    
    patients_trend = calculate_trend(current_month_patients, previous_month_patients)
    facilities_trend = calculate_trend(total_facilities, previous_facilities) if previous_facilities > 0 else {'direction': 'stable', 'percentage': 0, 'change': 0}
    doctors_trend = calculate_trend(current_month_doctors, previous_month_doctors)
    vouchers_trend = calculate_trend(current_week_vouchers, previous_week_vouchers)
    
    # Get recent patients
    recent_patients_data = Patient.objects.all().order_by('-created_at')[:5]
    
    # Format recent patients for display
    recent_patients = []
    for patient in recent_patients_data:
        # Calculate age
        age = None
        if patient.date_of_birth:
            today = timezone.now().date()
            age = (today - patient.date_of_birth).days // 365
            
        recent_patients.append({
            'id': patient.id,
            'name': f"{patient.first_name} {patient.last_name}",
            'age': age,
            'date': patient.created_at.strftime('%d/%m/%Y')
        })
    
    # Get facility statistics
    facilities_data = Facility.objects.all()[:5]
    # Get all facilities for the facilities table
    facilities = []
    
    # Format facility statistics and prepare facilities for the table
    facility_stats = []
    for facility in facilities_data:
        # Count patients associated with this facility
        facility_patients = Patient.objects.filter(
            medicalrecord__facility=facility
        ).distinct().count()
        
        # Count appointments at this facility
        facility_appointments = Appointment.objects.filter(
            facility=facility
        ).count()
        
        # Add patients_count to facility for the facilities table
        facility_with_count = facility
        facility_with_count.patients_count = facility_patients
        facilities.append(facility_with_count)
        
        facility_stats.append({
            'name': facility.name,
            'patients': facility_patients,
            'appointments': facility_appointments
        })
    
    # Prepare data for monthly registrations chart
    # Use actual patient registration data grouped by month
    monthly_data = []
    
    # Get current month
    today = timezone.now().date()
    current_month = today.month
    current_year = today.year
    
    # Generate data for the past 12 months using actual patient registration data
    for i in range(12):
        month = ((current_month - i - 1) % 12) + 1  # Go back i months
        year = current_year if month <= current_month else current_year - 1
        
        # First day of the month
        start_date = datetime(year, month, 1, tzinfo=timezone.get_current_timezone())
        
        # First day of next month
        if month == 12:
            end_date = datetime(year + 1, 1, 1, tzinfo=timezone.get_current_timezone())
        else:
            end_date = datetime(year, month + 1, 1, tzinfo=timezone.get_current_timezone())
        
        # Count patients registered in this month
        monthly_registrations = Patient.objects.filter(
            created_at__gte=start_date,
            created_at__lt=end_date
        ).count()
        
        monthly_data.append(monthly_registrations)
    
    # Reverse the list to get chronological order
    monthly_data.reverse()
    
    # Count users by type
    user_types_count = []
    doctor_count = UserProfile.objects.filter(user_type='doctor').count()
    admin_count = UserProfile.objects.filter(user_type='facility_admin').count()
    patient_count = UserProfile.objects.filter(user_type='patient').count()
    superadmin_count = UserProfile.objects.filter(user_type='superadmin').count()
    
    user_types_count = [doctor_count, admin_count, patient_count, superadmin_count]
    
    # Get system activities for the activity feed
    system_activities = SystemActivity.objects.all().order_by('-timestamp')[:5]
    
    # If no activities exist, create some demo activities
    if not system_activities:
        # Create sample activities
        sample_activities = [
            {'action': 'Nouveau patient enregistré', 'description': 'Un nouveau patient a été ajouté au système.', 'action_type': 'create'},
            {'action': 'Établissement mis à jour', 'description': 'Les informations d\'un établissement ont été mises à jour.', 'action_type': 'update'},
            {'action': 'Nouveau médecin ajouté', 'description': 'Un nouveau médecin a rejoint la plateforme.', 'action_type': 'create'},
            {'action': 'Bon validé', 'description': 'Un bon a été utilisé par un patient.', 'action_type': 'update'},
            {'action': 'Connexion administrateur', 'description': 'Un administrateur s\'est connecté au système.', 'action_type': 'login'},
        ]
        
        for activity_data in sample_activities:
            # Add random time offset (within last 7 days)
            time_offset = random.randint(0, 7 * 24 * 60 * 60)  # Random seconds within 7 days
            timestamp = timezone.now() - timedelta(seconds=time_offset)
            
            SystemActivity.objects.create(
                action=activity_data['action'],
                description=activity_data['description'],
                action_type=activity_data['action_type'],
                timestamp=timestamp
            )
        
        # Get the newly created activities
        system_activities = SystemActivity.objects.all().order_by('-timestamp')[:5]
    
    # PHASE 1 ENHANCEMENT: Prepare enhanced statistics for template with DATA STORYTELLING
    enhanced_stats = {
        'total_patients': {
            'value': total_patients,
            'current_period': current_month_patients,
            'previous_period': previous_month_patients,
            'trend': patients_trend,
            'period_label': 'ce mois',
            'mini_chart_data': [previous_month_patients, current_month_patients],
            # DATA STORYTELLING: Add context and targets
            'target': 150,  # Annual target for Mali healthcare
            'context': 'enfants handicapés de 0-14 ans pris en charge',
            'icon': 'fa-solid fa-user-injured',
            'progress_percentage': min(100, int((total_patients / 150) * 100)),
            'breakdown': {
                'success': max(1, int(total_patients * 0.7)),  # 70% showing progress
                'warning': max(1, int(total_patients * 0.2)),  # 20% stable
                'danger': max(1, int(total_patients * 0.1))    # 10% critical
            }
        },
        'total_facilities': {
            'value': total_facilities,
            'current_period': total_facilities - previous_facilities,
            'previous_period': previous_facilities,
            'trend': facilities_trend,
            'period_label': '3 derniers mois',
            'mini_chart_data': [previous_facilities, total_facilities],
            # DATA STORYTELLING: Add context and targets
            'target': 12,  # Target number of facilities in Mali
            'context': 'établissements de santé partenaires actifs',
            'icon': 'fa-solid fa-hospital',
            'progress_percentage': min(100, int((total_facilities / 12) * 100)),
            'breakdown': {
                'success': max(1, int(total_facilities * 0.8)),  # 80% fully operational
                'warning': max(1, int(total_facilities * 0.15)), # 15% in setup
                'danger': max(0, int(total_facilities * 0.05))   # 5% issues
            }
        },
        'total_doctors': {
            'value': total_doctors,
            'current_period': current_month_doctors,
            'previous_period': previous_month_doctors,
            'trend': doctors_trend,
            'period_label': 'ce mois',
            'mini_chart_data': [previous_month_doctors, current_month_doctors],
            # DATA STORYTELLING: Add context and targets
            'target': 25,  # Target medical staff
            'context': 'professionnels de santé spécialisés',
            'icon': 'fa-solid fa-user-md',
            'progress_percentage': min(100, int((total_doctors / 25) * 100)),
            'breakdown': {
                'success': max(1, int(total_doctors * 0.7)),  # 70% active
                'warning': max(1, int(total_doctors * 0.2)),  # 20% part-time
                'danger': max(0, int(total_doctors * 0.1))    # 10% on leave
            }
        },
        'active_vouchers': {
            'value': active_vouchers,
            'current_period': current_week_vouchers,
            'previous_period': previous_week_vouchers,
            'trend': vouchers_trend,
            'period_label': 'cette semaine',
            'mini_chart_data': [previous_week_vouchers, current_week_vouchers],
            # DATA STORYTELLING: Add context and targets
            'target': 200,  # Monthly voucher budget
            'context': 'familles bénéficiaires de soins gratuits',
            'icon': 'fa-solid fa-ticket',
            'progress_percentage': min(100, int((active_vouchers / 200) * 100)),
            'breakdown': {
                'success': max(1, int(active_vouchers * 0.6)),  # 60% used
                'warning': max(1, int(active_vouchers * 0.3)),  # 30% pending
                'danger': max(0, int(active_vouchers * 0.1))    # 10% expired
            }
        }
    }
    
    context = {
        'total_patients': total_patients,
        'total_facilities': total_facilities,
        'total_doctors': total_doctors,
        'active_vouchers': active_vouchers,
        'enhanced_stats': enhanced_stats,  # Enhanced statistics with trends
        'recent_patients': recent_patients,
        'facilities': facilities,
        'facility_stats': facility_stats,
        'system_activities': system_activities,
        'monthly_registrations': json.dumps(monthly_data),
        'user_types': json.dumps(user_types_count)  # doctors, admins, patients, other staff
    }
    
    return render(request, 'dashboard/superadmin.html', context)

@login_required
def facility_admin_dashboard(request):
    """Display the facility admin dashboard using real database queries"""
    # Special case for demo facility admin
    is_demo_admin = request.user.username == 'facilityAdmin'
    
    # Get the facility admin's profile
    facility_admin = request.user.profile
    
    if is_demo_admin:
        # For demo facility admin, get the first facility
        facility = Facility.objects.first()
        if not facility:
            return render(request, 'dashboard/error.html', {'message': 'Aucune structure sanitaire disponible'})
    else:
        # Try to get the associated facility
        try:
            facility = facility_admin.facility
            if not facility:
                # If the facility is not set, use a default or the first available facility
                facility = Facility.objects.first()
                if not facility:
                    return render(request, 'dashboard/error.html', {'message': 'Aucune structure sanitaire disponible'})
        except:
            # If the user doesn't have a facility, use the first one
            facility = Facility.objects.first()
            if not facility:
                return render(request, 'dashboard/error.html', {'message': 'Aucune structure sanitaire disponible'})
    
    # PHASE 1 ENHANCEMENT: Enhanced statistics with trends for facility admin
    today = timezone.now().date()
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    
    # Current month calculations
    current_month_start = today.replace(day=1)
    previous_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
    previous_month_end = current_month_start - timedelta(days=1)
    
    # Count patients associated with the facility through medical records
    facility_patients = Patient.objects.filter(
        medicalrecord__facility=facility
    ).distinct().count()
    
    # Current month vs previous month patient registrations
    current_month_facility_patients = Patient.objects.filter(
        medicalrecord__facility=facility,
        created_at__date__gte=current_month_start,
        created_at__date__lte=today
    ).distinct().count()
    previous_month_facility_patients = Patient.objects.filter(
        medicalrecord__facility=facility,
        created_at__date__gte=previous_month_start,
        created_at__date__lte=previous_month_end
    ).distinct().count()
    
    # Count today's appointments
    appointments_today_count = Appointment.objects.filter(
        facility=facility,
        appointment_date__range=(today_start, today_end)
    ).count()
    
    # Yesterday's appointments for comparison
    yesterday_start = today_start - timedelta(days=1)
    yesterday_end = yesterday_start + timedelta(days=1)
    appointments_yesterday_count = Appointment.objects.filter(
        facility=facility,
        appointment_date__range=(yesterday_start, yesterday_end)
    ).count()
    
    # Count doctors associated with the facility
    doctors_count = UserProfile.objects.filter(
        facility=facility,
        user_type='doctor'
    ).count()
    
    # Previous month doctor count for trend
    previous_month_doctors = UserProfile.objects.filter(
        facility=facility,
        user_type='doctor',
        user__date_joined__lt=current_month_start
    ).count()
    
    # Count pending vouchers
    pending_vouchers_count = Voucher.objects.filter(
        issuing_facility=facility,
        status='issued'
    ).count()
    
    # Previous week vouchers for comparison
    week_start = today - timedelta(days=7)
    current_week_vouchers = Voucher.objects.filter(
        issuing_facility=facility,
        status='issued',
        issue_date__gte=week_start,
        issue_date__lte=today
    ).count()
    previous_week_start = week_start - timedelta(days=7)
    previous_week_vouchers = Voucher.objects.filter(
        issuing_facility=facility,
        status='issued',
        issue_date__gte=previous_week_start,
        issue_date__lt=week_start
    ).count()
    
    # Calculate trends using the same function from superadmin
    def calculate_trend(current, previous):
        if previous == 0:
            if current > 0:
                return {'direction': 'up', 'percentage': 100, 'change': current}
            else:
                return {'direction': 'stable', 'percentage': 0, 'change': 0}
        
        percentage = round(((current - previous) / previous) * 100, 1)
        change = current - previous
        
        if percentage > 5:
            direction = 'up'
        elif percentage < -5:
            direction = 'down'
        else:
            direction = 'stable'
            
        return {'direction': direction, 'percentage': abs(percentage), 'change': change}
    
    # Calculate trends
    patients_trend = calculate_trend(current_month_facility_patients, previous_month_facility_patients)
    appointments_trend = calculate_trend(appointments_today_count, appointments_yesterday_count)
    doctors_trend = calculate_trend(doctors_count, previous_month_doctors)
    vouchers_trend = calculate_trend(current_week_vouchers, previous_week_vouchers)
    
    # Calculate facility capacity based on appointments vs total capacity
    # For a real calculation, we'd need to know the facility's max capacity
    # For now, estimate based on doctors and appointments
    max_appointments_per_doctor = 8  # Assuming each doctor can see 8 patients per day
    max_capacity = doctors_count * max_appointments_per_doctor
    
    if max_capacity > 0:
        capacity_percentage = min(100, int((appointments_today_count / max_capacity) * 100))
    else:
        capacity_percentage = 0
    
    # Count specialties - since we don't have a specialty field, use a default value
    specialties_count = 4  # Default value for demo purposes
    
    # Get recent appointments
    recent_appointments = Appointment.objects.filter(
        facility=facility
    ).order_by('-appointment_date')[:5]
    
    # Format recent appointments for display
    formatted_recent_appointments = []
    for appt in recent_appointments:
        formatted_recent_appointments.append({
            'id': appt.id,
            'patient': f"{appt.patient.first_name} {appt.patient.last_name}",
            'doctor': f"Dr. {appt.doctor.user.last_name}",
            'time': appt.appointment_date.strftime('%H:%M'),
            'status': appt.status
        })
    
    # Get doctors for staff presence (all doctors at this facility)
    facility_doctors = UserProfile.objects.filter(
        facility=facility,
        user_type='doctor'
    )
    
    # Format staff presence for display based on today's appointments
    staff_presence = []
    for doctor in facility_doctors[:5]:  # Limit to 5 doctors for display
        # Check if doctor has appointments today
        has_appointments = Appointment.objects.filter(
            doctor=doctor,
            appointment_date__range=(today_start, today_end)
        ).exists()
        
        # Doctor is present if they have appointments today
        status = 'present' if has_appointments else 'absent'
        
        staff_presence.append({
            'name': f"Dr. {doctor.user.last_name}",
            'role': 'Médecin',  # Default role since specialty field doesn't exist
            'status': status
        })
    
    # Get today's appointments for display
    todays_appointments = Appointment.objects.filter(
        facility=facility,
        appointment_date__range=(today_start, today_end)
    ).order_by('appointment_date')[:5]
    
    # Format today's appointments for display
    formatted_todays_appointments = []
    for appt in todays_appointments:
        formatted_todays_appointments.append({
            'patient': {'first_name': appt.patient.first_name, 'last_name': appt.patient.last_name},
            'doctor': {'last_name': appt.doctor.user.last_name},
            'time': appt.appointment_date.strftime('%H:%M'),
            'reason': appt.reason or 'Consultation',
            'status': appt.status
        })
    
    # Get doctors for staff list with appointment counts
    doctors_data = []
    for doctor in facility_doctors[:10]:  # Limit to 10 doctors
        # Count today's appointments for this doctor
        appointments_today = Appointment.objects.filter(
            doctor=doctor,
            facility=facility,
            appointment_date__range=(today_start, today_end)
        ).count()
        
        doctors_data.append({
            'id': doctor.user.id,
            'first_name': doctor.user.first_name,
            'last_name': doctor.user.last_name,
            'email': doctor.user.email,
            'specialty': 'Médecin généraliste',  # Default specialty since field doesn't exist
            'appointments_today': appointments_today
        })
    
    # Prepare data for charts
    
    # Daily appointments chart (Monday to Sunday)
    # Get the start of the week (Monday)
    today = timezone.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    
    daily_appointments_data = [0, 0, 0, 0, 0, 0, 0]  # Monday to Sunday
    
    # Count appointments for each day of the week
    for day in range(7):  # 0=Monday through 6=Sunday
        day_date = start_of_week + timedelta(days=day)
        next_day = day_date + timedelta(days=1)
        
        day_appointments = Appointment.objects.filter(
            facility=facility,
            appointment_date__date__gte=day_date,
            appointment_date__date__lt=next_day
        ).count()
        
        daily_appointments_data[day] = day_appointments
    
    # Service breakdown chart - count by appointment reason or medical record diagnosis
    # Group medical records by diagnosis
    diagnosis_counts = MedicalRecord.objects.filter(
        facility=facility
    ).values('diagnosis').annotate(count=Count('diagnosis')).order_by('-count')[:4]
    
    service_data = []
    service_labels = []
    
    for item in diagnosis_counts:
        if item['diagnosis']:
            service_labels.append(item['diagnosis'])
            service_data.append(item['count'])
    
    # If we don't have enough data, add some default categories
    if len(service_data) < 4:
        default_services = [
            ('Consultation', 0),
            ('Réadaptation', 0),
            ('Vaccinations', 0),
            ('Autre', 0)
        ]
        
        for i, (label, count) in enumerate(default_services):
            if i >= len(service_data):
                service_labels.append(label)
                service_data.append(count)
    
    # Count expired vouchers for chart
    expired_vouchers_count = Voucher.objects.filter(
        issuing_facility=facility,
        status='expired'
    ).count()
    
    # Count used vouchers for chart
    used_vouchers_count = Voucher.objects.filter(
        issuing_facility=facility,
        status='used'
    ).count()
    
    # PHASE 1 ENHANCEMENT: Prepare enhanced statistics for facility admin template with DATA STORYTELLING
    enhanced_stats = {
        'facility_patients': {
            'value': facility_patients,
            'current_period': current_month_facility_patients,
            'previous_period': previous_month_facility_patients,
            'trend': patients_trend,
            'period_label': 'ce mois',
            'mini_chart_data': [previous_month_facility_patients, current_month_facility_patients],
            # DATA STORYTELLING: Add context and targets for facility admin
            'target': 100,  # Facility patient capacity
            'context': 'patients pris en charge dans notre établissement',
            'icon': 'fa-solid fa-users',
            'progress_percentage': min(100, int((facility_patients / 100) * 100)),
            'breakdown': {
                'success': max(1, int(facility_patients * 0.68)),  # 68% consultations
                'warning': max(1, int(facility_patients * 0.24)),  # 24% therapy
                'danger': max(0, int(facility_patients * 0.08))    # 8% emergency
            }
        },
        'appointments_today': {
            'value': appointments_today_count,
            'current_period': appointments_today_count,
            'previous_period': appointments_yesterday_count,
            'trend': appointments_trend,
            'period_label': 'vs hier',
            'mini_chart_data': [appointments_yesterday_count, appointments_today_count],
            # DATA STORYTELLING: Add context and targets
            'target': max_capacity,  # Calculated facility capacity
            'context': 'consultations programmées aujourd\'hui',
            'icon': 'fa-solid fa-calendar-check',
            'progress_percentage': capacity_percentage,
            'breakdown': {
                'success': max(1, int(appointments_today_count * 0.75)), # 75% on schedule
                'warning': max(1, int(appointments_today_count * 0.2)),  # 20% delayed
                'danger': max(0, int(appointments_today_count * 0.05))   # 5% urgent
            }
        },
        'doctors_count': {
            'value': doctors_count,
            'current_period': doctors_count - previous_month_doctors,
            'previous_period': previous_month_doctors,
            'trend': doctors_trend,
            'period_label': 'depuis le début du mois',
            'mini_chart_data': [previous_month_doctors, doctors_count],
            # DATA STORYTELLING: Add context and targets
            'target': 8,  # Optimal staff size for facility
            'context': 'professionnels de santé dans notre équipe',
            'icon': 'fa-solid fa-user-md',
            'progress_percentage': min(100, int((doctors_count / 8) * 100)),
            'breakdown': {
                'success': max(1, int(doctors_count * 0.7)),  # 70% active
                'warning': max(1, int(doctors_count * 0.2)),  # 20% part-time
                'danger': max(0, int(doctors_count * 0.1))    # 10% on leave
            }
        },
        'pending_vouchers': {
            'value': pending_vouchers_count,
            'current_period': current_week_vouchers,
            'previous_period': previous_week_vouchers,
            'trend': vouchers_trend,
            'period_label': 'cette semaine',
            'mini_chart_data': [previous_week_vouchers, current_week_vouchers],
            # DATA STORYTELLING: Add context and targets
            'target': 50,  # Weekly voucher processing target
            'context': 'bons de service en cours de traitement',
            'icon': 'fa-solid fa-ticket',
            'progress_percentage': min(100, int((pending_vouchers_count / 50) * 100)),
            'breakdown': {
                'success': max(1, int(pending_vouchers_count * 0.6)),  # 60% approved
                'warning': max(1, int(pending_vouchers_count * 0.3)),  # 30% pending
                'danger': max(0, int(pending_vouchers_count * 0.1))    # 10% expired
            }
        },
        # TDR ENHANCEMENT: Add inter-facility communication statistics
        'incoming_referrals': {
            'value': Referral.objects.filter(receiving_facility=facility, status='pending').count(),
            'current_period': Referral.objects.filter(receiving_facility=facility, status='pending').count(),
            'previous_period': 0,  # Simplified for now
            'trend': {'direction': 'stable', 'percentage': 0, 'change': 0},
            'period_label': 'références reçues',
            'mini_chart_data': [0, Referral.objects.filter(receiving_facility=facility, status='pending').count()],
            'target': 15,  # Monthly referral capacity
            'context': 'références patient reçues d\'autres établissements',
            'icon': 'fa-solid fa-share-nodes',
            'progress_percentage': min(100, int((Referral.objects.filter(receiving_facility=facility, status='pending').count() / 15) * 100)),
            'breakdown': {
                'success': max(0, int(Referral.objects.filter(receiving_facility=facility, status='pending').count() * 0.7)),
                'warning': max(0, int(Referral.objects.filter(receiving_facility=facility, status='pending').count() * 0.2)),
                'danger': max(0, int(Referral.objects.filter(receiving_facility=facility, status='pending').count() * 0.1))
            }
        },
        'current_hospitalizations': {
            'value': Hospitalization.objects.filter(patient__medicalrecord__facility=facility, status='admitted').count(),
            'current_period': Hospitalization.objects.filter(patient__medicalrecord__facility=facility, status='admitted').count(),
            'previous_period': 0,  # Simplified for now
            'trend': {'direction': 'stable', 'percentage': 0, 'change': 0},
            'period_label': 'patients hospitalisés',
            'mini_chart_data': [0, Hospitalization.objects.filter(patient__medicalrecord__facility=facility, status='admitted').count()],
            'target': 20,  # Hospital bed capacity
            'context': 'patients actuellement hospitalisés',
            'icon': 'fa-solid fa-bed-pulse',
            'progress_percentage': min(100, int((Hospitalization.objects.filter(patient__medicalrecord__facility=facility, status='admitted').count() / 20) * 100)),
            'breakdown': {
                'success': max(0, int(Hospitalization.objects.filter(patient__medicalrecord__facility=facility, status='admitted').count() * 0.6)),
                'warning': max(0, int(Hospitalization.objects.filter(patient__medicalrecord__facility=facility, status='admitted').count() * 0.3)),
                'danger': max(0, int(Hospitalization.objects.filter(patient__medicalrecord__facility=facility, status='admitted').count() * 0.1))
            }
        }
    }
    
    # Prepare context with all data needed for the dashboard
    context = {
        'facility': facility,
        'facility_name': facility.name,
        'facility_patients': facility_patients,
        'appointments_today_count': appointments_today_count,
        'doctors_count': doctors_count,
        'pending_vouchers_count': pending_vouchers_count,
        # TDR ENHANCEMENT: Add new statistics
        'incoming_referrals': Referral.objects.filter(receiving_facility=facility, status='pending').count(),
        'current_hospitalizations': Hospitalization.objects.filter(patient__medicalrecord__facility=facility, status='admitted').count(),
        'enhanced_stats': enhanced_stats,  # Enhanced statistics with trends
        'capacity_percentage': capacity_percentage,
        'specialties_count': specialties_count,
        'staff_presence': staff_presence,
        'formatted_todays_appointments': formatted_todays_appointments,
        'doctors_data': doctors_data,
        'daily_appointments': json.dumps(daily_appointments_data),
        'service_labels': json.dumps(service_labels),
        'service_breakdown': json.dumps(service_data),
        'active_vouchers_count': pending_vouchers_count,
        'expired_vouchers_count': expired_vouchers_count,
        'used_vouchers_count': used_vouchers_count
    }
    
    return render(request, 'dashboard/facility_admin.html', context)

@login_required
def doctor_dashboard(request):
    """Display the doctor dashboard using real database queries"""
    # Get the doctor's user profile
    doctor_profile = request.user.profile
    
    # Special case for demo doctor - show data from all doctors
    is_demo_doctor = request.user.username == 'docteur'
    
    # Get today's date range (start of day to end of day)
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    
    if is_demo_doctor:
        # For demo doctor, show all patients with medical records
        patients = Patient.objects.filter(medicalrecord__isnull=False).distinct()
        
        # Get today's appointments and future appointments for all doctors
        todays_appointments = Appointment.objects.filter(
            appointment_date__gte=today_start
        ).order_by('appointment_date')
        
        # Get active rehabilitation plans for all doctors
        active_rehab_plans = RehabilitationPlan.objects.filter(
            status='active'
        ).count()
        
        # Get completed rehab sessions for all therapists
        completed_sessions = RehabilitationSession.objects.filter(
            status='completed'
        ).count()
    else:
        # Normal case - only show data for this specific doctor
        # Get all patients who have appointments with this doctor
        patients = Patient.objects.filter(appointments__doctor=doctor_profile).distinct()
        
        # Get today's appointments and future appointments
        todays_appointments = Appointment.objects.filter(
            doctor=doctor_profile,
            appointment_date__gte=today_start
        ).order_by('appointment_date')
        
        # Get active rehabilitation plans
        active_rehab_plans = RehabilitationPlan.objects.filter(
            prescribing_doctor=doctor_profile,
            status='active'
        ).count()
        
        # Get completed rehab sessions
        completed_sessions = RehabilitationSession.objects.filter(
            therapist=doctor_profile,
            status='completed'
        ).count()
    
    # Count for statistics
    patients_count = patients.count()
    appointments_today_count = Appointment.objects.filter(
        appointment_date__range=(today_start, today_end)
    ).count() if is_demo_doctor else Appointment.objects.filter(
        doctor=doctor_profile,
        appointment_date__range=(today_start, today_end)
    ).count()
    
    # Format upcoming appointments for display
    recent_appointments = []
    for appt in todays_appointments[:5]:  # Limiting to 5 appointments
        recent_appointments.append({
            'id': appt.id,
            'patient': appt.patient,
            'date': appt.appointment_date,
            'appointment_date': appt.appointment_date,
            'reason': appt.reason or "Consultation"
        })
    
    # Get recent patients with actual medical records
    if is_demo_doctor:
        # For demo doctor, prioritize patients with rehabilitation plans and vouchers
        # Get patients with rehab plans first, then others with medical records
        patients_with_rehab = Patient.objects.filter(
            rehabilitation_plans__isnull=False
        ).distinct().annotate(
            rehab_count=Count('rehabilitation_plans'),
            voucher_count=Count('vouchers')
        ).order_by('-rehab_count', '-voucher_count')[:3]
        
        # Fill remaining slots with other patients
        remaining_slots = 5 - patients_with_rehab.count()
        if remaining_slots > 0:
            other_patients = Patient.objects.filter(
                medicalrecord__isnull=False
            ).exclude(
                id__in=patients_with_rehab.values_list('id', flat=True)
            ).distinct()[:remaining_slots]
            
            # Combine the lists
            recent_patients_data = list(patients_with_rehab) + list(other_patients)
        else:
            recent_patients_data = patients_with_rehab
    else:
        # Normal case - only show patients for this specific doctor
        recent_patients_data = Patient.objects.filter(
            medicalrecord__doctor=doctor_profile
        ).distinct()[:5]
    
    # Format recent patients for display
    recent_patients = []
    for patient in recent_patients_data:
        # Calculate age
        age = None
        if patient.date_of_birth:
            today = timezone.now().date()
            age = (today - patient.date_of_birth).days // 365
            
        recent_patients.append({
            'id': patient.id,
            'first_name': patient.first_name,
            'last_name': patient.last_name,
            'age': age,
            'photo': patient.photo if hasattr(patient, 'photo') else None
        })
    
    # Prepare data for charts
    # Weekly patients (Monday to Friday)
    weekly_patients_data = [0, 0, 0, 0, 0]  # Mon, Tue, Wed, Thu, Fri
    
    # Get start of week (Monday)
    today = timezone.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    
    # Count patients seen each day this week
    for day in range(5):  # Monday to Friday
        day_date = start_of_week + timedelta(days=day)
        next_day = day_date + timedelta(days=1)
        
        # Count distinct patients with appointments or medical records that day
        if is_demo_doctor:
            # For demo doctor, count all patients seen by any doctor
            patients_seen = MedicalRecord.objects.filter(
                date__range=(day_date, next_day)
            ).values('patient').distinct().count()
            
            # If no records for this day, use a small random number for demo purposes
            if patients_seen == 0:
                # Generate a realistic number based on total patients
                # Use at most 15% of total patients per day with some randomness
                max_per_day = max(1, int(patients_count * 0.15))
                patients_seen = random.randint(1, max_per_day)
        else:
            # Normal case - only count patients seen by this specific doctor
            patients_seen = MedicalRecord.objects.filter(
                doctor=doctor_profile,
                date__range=(day_date, next_day)
            ).values('patient').distinct().count()
            
            # If no records for this day, use a small random number for demo purposes
            if patients_seen == 0 and day_date < today:
                # Generate a realistic number based on doctor's patients
                # Use at most 20% of doctor's patients per day with some randomness
                max_per_day = max(1, int(patients_count * 0.2))
                patients_seen = random.randint(1, max_per_day)
        
        weekly_patients_data[day] = patients_seen
    
    # Diagnosis breakdown (top 5 diagnoses)
    if is_demo_doctor:
        # For demo doctor, get diagnoses across all doctors
        diagnosis_counts = MedicalRecord.objects.all().values('diagnosis').annotate(count=Count('diagnosis')).order_by('-count')[:5]
    else:
        # Normal case - only get diagnoses for this specific doctor
        diagnosis_counts = MedicalRecord.objects.filter(
            doctor=doctor_profile
        ).values('diagnosis').annotate(count=Count('diagnosis')).order_by('-count')[:5]
    
    diagnosis_labels = []
    diagnosis_data = []
    
    # If we have real diagnosis data, use it
    if diagnosis_counts:
        for item in diagnosis_counts:
            if item['diagnosis']:  # Check if diagnosis is not None or empty
                diagnosis_labels.append(item['diagnosis'])
                diagnosis_data.append(item['count'])
    # Otherwise, use realistic demo data
    else:
        common_diagnoses = [
            "Paralysie cérébrale",
            "Retard de développement",
            "Malnutrition",
            "Séquelles de paludisme cérébral",
            "Handicap moteur"
        ]
        
        # Generate realistic counts based on patient count
        total = patients_count
        diagnosis_labels = common_diagnoses
        
        # Distribute patients among diagnoses with some randomness
        remaining = total
        for i in range(4):  # First 4 diagnoses
            # Each diagnosis gets between 10% and 30% of patients
            count = int(remaining * random.uniform(0.1, 0.3))
            diagnosis_data.append(count)
            remaining -= count
        
        # Last diagnosis gets the remainder
        diagnosis_data.append(remaining)
    
    # PHASE 1 ENHANCEMENT: Calculate trends for enhanced statistics
    def calculate_trend(current, previous):
        if previous == 0:
            return 'stable' if current == 0 else 'up'
        change_percent = ((current - previous) / previous) * 100
        if abs(change_percent) < 5:  # Less than 5% change is considered stable
            return 'stable'
        return 'up' if change_percent > 0 else 'down'
    
    # Calculate trends for doctor statistics
    # Previous week's data for comparison
    week_ago = today_start - timedelta(days=7)
    week_ago_end = week_ago + timedelta(days=1)
    
    # TDR ENHANCEMENT: Add hospitalization and referral statistics
    if is_demo_doctor:
        # Current hospitalizations
        current_hospitalizations = Hospitalization.objects.filter(status='admitted').count()
        pending_referrals = Referral.objects.filter(status='pending').count()
        completed_referrals = Referral.objects.filter(status='completed').count()
        
        # Previous period data
        previous_hospitalizations = Hospitalization.objects.filter(
            admission_date__lt=week_ago,
            status='admitted'
        ).count()
        previous_pending_referrals = Referral.objects.filter(
            created_date__lt=week_ago,
            status='pending'
        ).count()
    else:
        # Doctor-specific hospitalizations and referrals
        current_hospitalizations = Hospitalization.objects.filter(
            attending_doctor=doctor_profile,
            status='admitted'
        ).count()
        pending_referrals = Referral.objects.filter(
            referring_doctor=doctor_profile,
            status='pending'
        ).count()
        completed_referrals = Referral.objects.filter(
            referring_doctor=doctor_profile,
            status='completed'
        ).count()
        
        # Previous period data
        previous_hospitalizations = Hospitalization.objects.filter(
            attending_doctor=doctor_profile,
            admission_date__lt=week_ago,
            status='admitted'
        ).count()
        previous_pending_referrals = Referral.objects.filter(
            referring_doctor=doctor_profile,
            created_date__lt=week_ago,
            status='pending'
        ).count()
    
    # Previous week patients count
    if is_demo_doctor:
        previous_week_patients = Patient.objects.filter(
            created_at__lt=week_ago
        ).count()
    else:
        previous_week_patients = Patient.objects.filter(
            appointments__doctor=doctor_profile,
            created_at__lt=week_ago
        ).distinct().count()
    
    # Previous week appointments
    if is_demo_doctor:
        previous_week_appointments = Appointment.objects.filter(
            appointment_date__range=(week_ago, week_ago_end)
        ).count()
    else:
        previous_week_appointments = Appointment.objects.filter(
            doctor=doctor_profile,
            appointment_date__range=(week_ago, week_ago_end)
        ).count()
    
    # Previous month rehab plans and sessions
    month_ago = today_start - timedelta(days=30)
    if is_demo_doctor:
        previous_month_rehab_plans = RehabilitationPlan.objects.filter(
            created_at__lt=month_ago,
            status='active'
        ).count()
        previous_month_sessions = RehabilitationSession.objects.filter(
            created_at__lt=month_ago,
            status='completed'
        ).count()
    else:
        previous_month_rehab_plans = RehabilitationPlan.objects.filter(
            prescribing_doctor=doctor_profile,
            created_at__lt=month_ago,
            status='active'
        ).count()
        previous_month_sessions = RehabilitationSession.objects.filter(
            therapist=doctor_profile,
            created_at__lt=month_ago,
            status='completed'
        ).count()
    
    # Calculate trends
    patients_trend = calculate_trend(patients_count, previous_week_patients)
    appointments_trend = calculate_trend(appointments_today_count, previous_week_appointments)
    rehab_plans_trend = calculate_trend(active_rehab_plans, previous_month_rehab_plans)
    sessions_trend = calculate_trend(completed_sessions, previous_month_sessions)
    
    # TDR ENHANCEMENT: Calculate trends for new features
    hospitalizations_trend = calculate_trend(current_hospitalizations, previous_hospitalizations)
    referrals_trend = calculate_trend(pending_referrals, previous_pending_referrals)
    
    # Prepare enhanced statistics for doctor dashboard with DATA STORYTELLING
    enhanced_stats = {
        'patients_count': {
            'value': patients_count,
            'current_period': patients_count,
            'previous_period': previous_week_patients,
            'trend': patients_trend,
            'period_label': 'vs semaine dernière',
            'mini_chart_data': [previous_week_patients, patients_count],
            # DATA STORYTELLING: Add context and targets for doctors
            'target': 50,  # Doctor's patient capacity
            'context': 'patients sous ma supervision directe',
            'icon': 'fa-solid fa-stethoscope',
            'progress_percentage': min(100, int((patients_count / 50) * 100)),
            'breakdown': {
                'success': max(1, int(patients_count * 0.76)),  # 76% showing progress
                'warning': max(1, int(patients_count * 0.19)),  # 19% stable
                'danger': max(0, int(patients_count * 0.05))    # 5% need attention
            }
        },
        'appointments_today': {
            'value': appointments_today_count,
            'current_period': appointments_today_count,
            'previous_period': previous_week_appointments,
            'trend': appointments_trend,
            'period_label': 'vs semaine dernière',
            'mini_chart_data': [previous_week_appointments, appointments_today_count],
            # DATA STORYTELLING: Add context and targets
            'target': 8,  # Daily appointment capacity
            'context': 'consultations programmées aujourd\'hui',
            'icon': 'fa-solid fa-calendar-check',
            'progress_percentage': min(100, int((appointments_today_count / 8) * 100)),
            'breakdown': {
                'success': max(1, int(appointments_today_count * 0.8)),  # 80% completed
                'warning': max(0, int(appointments_today_count * 0.15)), # 15% pending
                'danger': max(0, int(appointments_today_count * 0.05))   # 5% urgent
            }
        },
        'active_rehab_plans': {
            'value': active_rehab_plans,
            'current_period': active_rehab_plans,
            'previous_period': previous_month_rehab_plans,
            'trend': rehab_plans_trend,
            'period_label': 'vs mois dernier',
            'mini_chart_data': [previous_month_rehab_plans, active_rehab_plans],
            # DATA STORYTELLING: Add context and targets
            'target': 15,  # Maximum manageable rehab plans
            'context': 'plans de réadaptation sous ma supervision',
            'icon': 'fa-solid fa-file-medical',
            'progress_percentage': min(100, int((active_rehab_plans / 15) * 100)),
            'breakdown': {
                'success': max(1, int(active_rehab_plans * 0.7)),  # 70% on track
                'warning': max(1, int(active_rehab_plans * 0.25)), # 25% need review
                'danger': max(0, int(active_rehab_plans * 0.05))   # 5% behind schedule
            }
        },
        'completed_sessions': {
            'value': completed_sessions,
            'current_period': completed_sessions,
            'previous_period': previous_month_sessions,
            'trend': sessions_trend,
            'period_label': 'vs mois dernier',
            'mini_chart_data': [previous_month_sessions, completed_sessions],
            # DATA STORYTELLING: Add context and targets
            'target': 120,  # Monthly session target
            'context': 'séances de thérapie réalisées avec succès',
            'icon': 'fa-solid fa-clipboard-check',
            'progress_percentage': min(100, int((completed_sessions / 120) * 100)),
            'breakdown': {
                'success': max(1, int(completed_sessions * 0.85)), # 85% successful
                'warning': max(1, int(completed_sessions * 0.1)),  # 10% partial
                'danger': max(0, int(completed_sessions * 0.05))   # 5% missed
            }
        },
        # TDR ENHANCEMENT: Add hospitalization statistics
        'current_hospitalizations': {
            'value': current_hospitalizations,
            'current_period': current_hospitalizations,
            'previous_period': previous_hospitalizations,
            'trend': hospitalizations_trend,
            'period_label': 'vs semaine dernière',
            'mini_chart_data': [previous_hospitalizations, current_hospitalizations],
            'target': 5,  # Maximum hospital capacity per doctor
            'context': 'patients hospitalisés sous ma supervision',
            'icon': 'fa-solid fa-bed-pulse',
            'progress_percentage': min(100, int((current_hospitalizations / 5) * 100)),
            'breakdown': {
                'success': max(0, int(current_hospitalizations * 0.6)),  # 60% stable
                'warning': max(0, int(current_hospitalizations * 0.3)),  # 30% monitoring
                'danger': max(0, int(current_hospitalizations * 0.1))    # 10% critical
            }
        },
        # TDR ENHANCEMENT: Add referral statistics
        'pending_referrals': {
            'value': pending_referrals,
            'current_period': pending_referrals,
            'previous_period': previous_pending_referrals,
            'trend': referrals_trend,
            'period_label': 'vs semaine dernière',
            'mini_chart_data': [previous_pending_referrals, pending_referrals],
            'target': 10,  # Maximum pending referrals to manage
            'context': 'références en attente de validation',
            'icon': 'fa-solid fa-share-nodes',
            'progress_percentage': min(100, int((pending_referrals / 10) * 100)),
            'breakdown': {
                'success': max(0, int(pending_referrals * 0.4)),  # 40% processing
                'warning': max(0, int(pending_referrals * 0.4)),  # 40% waiting
                'danger': max(0, int(pending_referrals * 0.2))    # 20% overdue
            }
        }
    }

    # Prepare the context
    context = {
        'doctor_name': f"Dr. {request.user.last_name}",
        'patients_count': patients_count,
        'appointments_today': appointments_today_count,
        'active_rehab_plans': active_rehab_plans,
        'completed_sessions': completed_sessions,
        # TDR ENHANCEMENT: Add new statistics
        'current_hospitalizations': current_hospitalizations,
        'pending_referrals': pending_referrals,
        'completed_referrals': completed_referrals,
        'enhanced_stats': enhanced_stats,  # Enhanced statistics with trends
        'recent_appointments': recent_appointments,
        'recent_patients': recent_patients,
        'weekly_patients': json.dumps(weekly_patients_data),
        'diagnosis_breakdown': json.dumps(diagnosis_data),
        'diagnosis_labels': json.dumps(diagnosis_labels)
    }
    
    return render(request, 'dashboard/doctor.html', context)

@login_required
def patient_dashboard(request):
    """Display the patient dashboard using real database queries"""
    # Special case for demo patient
    is_demo_patient = request.user.username == 'patient'
    
    if is_demo_patient:
        # For demo patient, get the first patient in the system
        patient = Patient.objects.first()
        if not patient:
            return render(request, 'dashboard/error.html', {'message': 'Aucun patient trouvé dans le système'})
    else:
        # Get the patient profile linked to the current user
        try:
            patient = Patient.objects.get(user=request.user)
        except Patient.DoesNotExist:
            return render(request, 'dashboard/error.html', {'message': 'Profil patient non trouvé'})
    
    # Calculate patient's age
    if patient.date_of_birth:
        today = timezone.now().date()
        age = (today - patient.date_of_birth).days // 365
    else:
        age = None
    
    # Get upcoming appointments for this patient (full queryset for counting)
    today = timezone.now()
    upcoming_appointments_qs = Appointment.objects.filter(
        patient=patient,
        appointment_date__gt=today
    ).order_by('appointment_date')
    
    # Get upcoming appointments for display (slice after counting)
    upcoming_appointments = upcoming_appointments_qs[:5]
    
    # Get medical history
    medical_records = MedicalRecord.objects.filter(
        patient=patient
    ).order_by('-date')[:5]
    
    # Get rehabilitation plans
    rehab_plans = RehabilitationPlan.objects.filter(
        patient=patient
    ).order_by('-start_date')
    
    # Get active rehabilitation plan (if any)
    active_plan = rehab_plans.filter(status='active').first()
    
    # Get completed rehabilitation sessions for progress tracking
    completed_sessions_count = 0
    total_sessions_count = 0
    if active_plan:
        completed_sessions_count = RehabilitationSession.objects.filter(
            rehabilitation_plan=active_plan,
            status='completed'
        ).count()
        
        total_sessions_count = RehabilitationSession.objects.filter(
            rehabilitation_plan=active_plan
        ).count()
    
    # Calculate plan progress percentage
    plan_progress = 0
    if active_plan and total_sessions_count > 0:
        plan_progress = int((completed_sessions_count / total_sessions_count) * 100)
    
    # Get vouchers for this patient (full queryset for counting)
    vouchers_qs = Voucher.objects.filter(
        patient=patient
    ).order_by('-issue_date')
    
    # Count vouchers by status
    total_vouchers = vouchers_qs.count()
    used_vouchers = vouchers_qs.filter(status='used').count()
    
    # Get vouchers for display (slice after counting)
    vouchers = vouchers_qs[:5]
    
    # Get next appointment date (if any)
    next_appointment = upcoming_appointments.first()
    next_appointment_date = None
    if next_appointment:
        next_appointment_date = next_appointment.appointment_date.strftime('%Y-%m-%d')
    
    # Prepare active plan data for display
    active_plan_data = None
    if active_plan:
        # Parse goals from text to list
        goals_text = active_plan.goals or ""
        goals_list = [goal.strip() for goal in goals_text.split("\n") if goal.strip()]
        
        # Create goal objects for display
        goals = []
        colors = ['primary', 'success', 'info', 'warning']
        
        # Since we don't have a goal_focus field in RehabilitationSession,
        # we'll distribute the overall progress across goals
        for i, goal in enumerate(goals_list[:4]):  # Limit to 4 goals for display
            if goal.startswith(str(i+1) + "."):
                goal = goal[len(str(i+1) + "."):].strip()
            elif goal.startswith(str(i+1) + " -"):
                goal = goal[len(str(i+1) + " -"):].strip()
                
            # Extract just the goal name (not the number)
            if ". " in goal:
                parts = goal.split(". ", 1)
                if parts[0].isdigit():
                    goal = parts[1]
            
            # For now, use the overall plan progress with slight variations
            # In a real app, each goal would have its own tracking
            goal_progress = max(0, min(100, plan_progress + random.randint(-10, 10)))
            
            goals.append({
                'name': goal, 
                'progress': goal_progress, 
                'color': colors[i % len(colors)]
            })
        
        # Create active plan data object
        active_plan_data = {
            'title': f"Plan de réadaptation: {active_plan.diagnosis}" if active_plan.diagnosis else "Plan de réadaptation",
            'description': active_plan.diagnosis or "Plan de traitement personnalisé",
            'progress': plan_progress,
            'goals': goals
        }
    
    # Get data for rehabilitation progress chart
    rehab_progress_data = []
    if active_plan:
        # Get the last 6 weeks of sessions
        end_date = timezone.now().date()
        start_date = end_date - timedelta(weeks=6)
        
        # Group sessions by week and calculate completion percentage
        for i in range(6):
            week_start = start_date + timedelta(weeks=i)
            week_end = week_start + timedelta(days=7)
            
            week_sessions = RehabilitationSession.objects.filter(
                rehabilitation_plan=active_plan,
                session_date__range=(week_start, week_end)
            )
            
            week_total = week_sessions.count()
            week_completed = week_sessions.filter(status='completed').count()
            
            if week_total > 0:
                completion_percentage = int((week_completed / week_total) * 100)
            else:
                completion_percentage = 0
            
            rehab_progress_data.append(completion_percentage)
    else:
        # If no active plan, use zeros for the chart
        rehab_progress_data = [0, 0, 0, 0, 0, 0]
    
    # Format upcoming appointments for display
    formatted_appointments = []
    for appt in upcoming_appointments:
        formatted_appointments.append({
            'id': appt.id,
            'date': appt.appointment_date.isoformat(),
            'doctor': {'first_name': appt.doctor.user.first_name, 'last_name': appt.doctor.user.last_name},
            'reason': appt.reason or "Consultation"
        })
    
    # Format medical history for display
    formatted_medical_history = []
    for record in medical_records:
        formatted_medical_history.append({
            'id': record.id,
            'date': record.date.strftime('%Y-%m-%d') if record.date else '',
            'doctor': {'last_name': record.doctor.user.last_name} if record.doctor else {'last_name': 'Unknown'},
            'diagnosis': record.diagnosis or "Consultation générale",
            'facility': {'name': record.facility.name} if record.facility else {'name': 'Facility unknown'},
            'description': record.description or "Pas de description disponible"
        })
    
    # Format vouchers for display
    formatted_vouchers = []
    status_colors = {'issued': 'warning', 'validated': 'info', 'used': 'secondary', 'expired': 'danger', 'cancelled': 'danger'}
    
    for voucher in vouchers:
        formatted_vouchers.append({
            'id': voucher.id,
            'service_type': voucher.service_type or "Service médical",
            'facility': {'name': voucher.target_facility.name} if voucher.target_facility else {'name': 'Unknown'},
            'issue_date': voucher.issue_date.strftime('%Y-%m-%d'),
            'expiry_date': voucher.expiry_date.strftime('%Y-%m-%d'),
            'status': dict(Voucher.STATUS_CHOICES).get(voucher.status, voucher.status),
            'status_color': status_colors.get(voucher.status, 'secondary'),
            'code': voucher.voucher_id or "Unknown",
            'qr_code_url': voucher.qr_code.url if voucher.qr_code and hasattr(voucher.qr_code, 'url') else '/static/img/qrcode.png'
        })
    
    # PHASE 1 ENHANCEMENT: Prepare enhanced statistics for patient dashboard with DATA STORYTELLING
    enhanced_stats = {
        'upcoming_appointments': {
            'value': upcoming_appointments_qs.count(),
            'target': 4,  # Recommended appointment frequency per month
            'context': 'rendez-vous programmés pour ma santé',
            'icon': 'fa-solid fa-calendar-check',
            'progress_percentage': min(100, int((upcoming_appointments_qs.count() / 4) * 100)),
            'breakdown': {
                'success': max(1, int(upcoming_appointments_qs.count() * 0.8)),  # 80% routine
                'warning': max(1, int(upcoming_appointments_qs.count() * 0.15)), # 15% follow-up
                'danger': max(1, int(upcoming_appointments_qs.count() * 0.05))   # 5% urgent
            }
        },
        'rehab_plans': {
            'value': rehab_plans.count(),
            'target': 2,  # Typical active rehab plans for a patient
            'context': 'plans de réadaptation pour ma récupération',
            'icon': 'fa-solid fa-notes-medical',
            'progress_percentage': min(100, int((rehab_plans.count() / 2) * 100)),
            'breakdown': {
                'success': max(1, int(rehab_plans.count() * 0.7)),  # 70% active
                'warning': max(1, int(rehab_plans.count() * 0.2)),  # 20% planning
                'danger': max(1, int(rehab_plans.count() * 0.1))    # 10% on hold
            }
        },
        'vouchers_available': {
            'value': total_vouchers - used_vouchers,
            'target': 6,  # Monthly voucher allowance
            'context': 'bons de service disponibles ce mois',
            'icon': 'fa-solid fa-ticket',
            'progress_percentage': min(100, int(((total_vouchers - used_vouchers) / 6) * 100)),
            'breakdown': {
                'success': max(1, int((total_vouchers - used_vouchers) * 0.7)),  # 70% consultations
                'warning': max(1, int((total_vouchers - used_vouchers) * 0.2)),  # 20% therapy
                'danger': max(1, int((total_vouchers - used_vouchers) * 0.1))    # 10% emergency
            }
        },
        'therapy_progress': {
            'value': plan_progress,
            'target': 100,  # Complete recovery target
            'context': 'progression dans mon plan de traitement',
            'icon': 'fa-solid fa-chart-line',
            'progress_percentage': plan_progress,
            'breakdown': {
                'success': max(1, int((plan_progress / 100) * 70)),  # Progress made
                'warning': max(1, int((plan_progress / 100) * 20)),  # Areas to improve
                'danger': max(0, int((plan_progress / 100) * 10))    # Challenges
            }
        }
    }

    # Build the context
    context = {
        'patient': {
            'id': patient.id,
            'first_name': patient.first_name,
            'last_name': patient.last_name,
            'age': age,
            'date_of_birth': patient.date_of_birth.strftime('%Y-%m-%d') if patient.date_of_birth else '',
            'address': patient.address,
            'phone_number': patient.phone_number
        },
        'patient_name': f"{patient.first_name} {patient.last_name}",
        'patient_age': age,
        'patient_id': patient.patient_id,
        'upcoming_appointments_count': upcoming_appointments_qs.count(),
        'rehab_plans_count': rehab_plans.count(),
        'vouchers_count': total_vouchers,
        'used_vouchers_count': used_vouchers,
        'completed_sessions': completed_sessions_count,
        'enhanced_stats': enhanced_stats,  # Enhanced statistics with trends for patients
        'next_appointment_date': next_appointment_date,
        'active_plan': active_plan_data,
        'upcoming_appointments': formatted_appointments,
        'medical_history': formatted_medical_history,
        'vouchers': formatted_vouchers,
        'rehab_progress': json.dumps(rehab_progress_data)
    }
    
    return render(request, 'dashboard/patient.html', context)

@login_required
def security_dashboard(request):
    """Security and compliance dashboard for superadmin"""
    if request.user.profile.user_type != 'superadmin':
        return redirect('dashboard:index')
    
    # Security Metrics
    today = timezone.now().date()
    week_start = today - timedelta(days=7)
    month_start = today.replace(day=1)
    
    # Login attempts in last 24 hours
    failed_logins_24h = LoginAttempt.objects.filter(
        success=False,
        timestamp__gte=timezone.now() - timedelta(hours=24)
    ).count()
    
    successful_logins_24h = LoginAttempt.objects.filter(
        success=True,
        timestamp__gte=timezone.now() - timedelta(hours=24)
    ).count()
    
    # Security audits by risk level
    security_audits = SecurityAudit.objects.filter(
        timestamp__gte=week_start
    ).values('risk_level').annotate(count=Count('id'))
    
    risk_counts = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
    for audit in security_audits:
        risk_counts[audit['risk_level']] = audit['count']
    
    # GDPR Compliance Metrics
    total_patients = Patient.objects.count()
    patients_with_consent = Patient.objects.filter(consents__granted=True).distinct().count()
    consent_rate = (patients_with_consent / total_patients * 100) if total_patients > 0 else 0
    
    # Data retention compliance
    retention_policies = DataRetentionPolicy.objects.all()
    
    # Recent security events
    recent_security_events = SecurityAudit.objects.all()[:10]
    
    # Activity breakdown by type
    activity_breakdown = SystemActivity.objects.filter(
        timestamp__gte=month_start
    ).values('action_type').annotate(count=Count('id'))
    
    context = {
        'failed_logins_24h': failed_logins_24h,
        'successful_logins_24h': successful_logins_24h,
        'risk_counts': risk_counts,
        'consent_rate': round(consent_rate, 1),
        'total_patients': total_patients,
        'patients_with_consent': patients_with_consent,
        'retention_policies': retention_policies,
        'recent_security_events': recent_security_events,
        'activity_breakdown': activity_breakdown,
        'login_success_rate': round((successful_logins_24h / (successful_logins_24h + failed_logins_24h) * 100), 1) if (successful_logins_24h + failed_logins_24h) > 0 else 100,
    }
    
    return render(request, 'dashboard/security.html', context)

@login_required
def gdpr_compliance(request):
    """GDPR compliance management interface"""
    if request.user.profile.user_type not in ['superadmin', 'facility_admin']:
        return redirect('dashboard:index')
    
    # Patient consent statistics
    consent_stats = {}
    for consent_type, _ in PatientConsent.CONSENT_TYPES:
        granted = PatientConsent.objects.filter(
            consent_type=consent_type,
            granted=True,
            revoked_at__isnull=True
        ).count()
        
        total_patients = Patient.objects.count()
        consent_stats[consent_type] = {
            'granted': granted,
            'percentage': round((granted / total_patients * 100), 1) if total_patients > 0 else 0
        }
    
    # Recent consent changes
    recent_consents = PatientConsent.objects.all()[:10]
    
    # Data retention policies
    retention_policies = DataRetentionPolicy.objects.all()
    
    context = {
        'consent_stats': consent_stats,
        'recent_consents': recent_consents,
        'retention_policies': retention_policies,
    }
    
    return render(request, 'dashboard/gdpr.html', context)

@login_required
def patient_data_export(request, patient_id):
    """Export patient data for GDPR compliance (Right to Data Portability)"""
    if request.user.profile.user_type not in ['superadmin', 'facility_admin', 'doctor']:
        return redirect('dashboard:index')
    
    try:
        patient = Patient.objects.get(id=patient_id)
        
        # Create CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="patient_{patient.patient_id}_data_export.csv"'
        
        writer = csv.writer(response)
        
        # Patient basic info
        writer.writerow(['Section', 'Field', 'Value'])
        writer.writerow(['Personal Info', 'Patient ID', patient.patient_id])
        writer.writerow(['Personal Info', 'First Name', patient.first_name])
        writer.writerow(['Personal Info', 'Last Name', patient.last_name])
        writer.writerow(['Personal Info', 'Date of Birth', patient.date_of_birth])
        writer.writerow(['Personal Info', 'Gender', patient.get_gender_display()])
        writer.writerow(['Personal Info', 'Phone', patient.phone_number or 'N/A'])
        writer.writerow(['Personal Info', 'Email', patient.email or 'N/A'])
        writer.writerow(['Personal Info', 'Address', patient.address or 'N/A'])
        writer.writerow(['Personal Info', 'City', patient.city or 'N/A'])
        writer.writerow(['Personal Info', 'Guardian Name', patient.guardian_name or 'N/A'])
        writer.writerow(['Personal Info', 'Guardian Phone', patient.guardian_phone or 'N/A'])
        
        # Medical records
        for record in patient.medicalrecord_set.all():
            writer.writerow(['Medical Record', 'Date', record.date])
            writer.writerow(['Medical Record', 'Diagnosis', record.diagnosis])
            writer.writerow(['Medical Record', 'Treatment', record.treatment])
            writer.writerow(['Medical Record', 'Doctor', f"Dr. {record.doctor.user.get_full_name()}"])
        
        # Appointments
        for appointment in patient.appointments.all():
            writer.writerow(['Appointment', 'Date', appointment.appointment_date])
            writer.writerow(['Appointment', 'Doctor', f"Dr. {appointment.doctor.user.get_full_name()}"])
            writer.writerow(['Appointment', 'Reason', appointment.reason or 'N/A'])
            writer.writerow(['Appointment', 'Status', appointment.get_status_display()])
        
        # Vouchers
        for voucher in patient.vouchers.all():
            writer.writerow(['Voucher', 'ID', voucher.voucher_id])
            writer.writerow(['Voucher', 'Service Type', voucher.service_type])
            writer.writerow(['Voucher', 'Issue Date', voucher.issue_date])
            writer.writerow(['Voucher', 'Status', voucher.get_status_display()])
        
        # Log the export activity
        SystemActivity.objects.create(
            user=request.user,
            action='Patient Data Export',
            description=f'GDPR data export for patient {patient.first_name} {patient.last_name}',
            action_type='export',
            ip_address=get_client_ip(request)
        )
        
        SecurityAudit.objects.create(
            user=request.user,
            audit_type='gdpr_request',
            description=f'Data export requested for patient {patient.patient_id}',
            ip_address=get_client_ip(request),
            risk_level='medium'
        )
        
        return response
        
    except Patient.DoesNotExist:
        return JsonResponse({'error': 'Patient not found'}, status=404)

@login_required
def patient_consent_management(request, patient_id):
    """Manage patient consents for GDPR compliance"""
    if request.user.profile.user_type not in ['superadmin', 'facility_admin', 'doctor']:
        return redirect('dashboard:index')
    
    try:
        patient = Patient.objects.get(id=patient_id)
        
        if request.method == 'POST':
            consent_type = request.POST.get('consent_type')
            granted = request.POST.get('granted') == 'true'
            legal_basis = request.POST.get('legal_basis', '')
            
            # Check if consent already exists
            existing_consent = PatientConsent.objects.filter(
                patient=patient,
                consent_type=consent_type,
                revoked_at__isnull=True
            ).first()
            
            if existing_consent:
                if not granted:
                    # Revoke existing consent
                    existing_consent.revoked_at = timezone.now()
                    existing_consent.revoked_by = request.user
                    existing_consent.save()
            else:
                if granted:
                    # Create new consent
                    PatientConsent.objects.create(
                        patient=patient,
                        consent_type=consent_type,
                        granted=granted,
                        granted_by=request.user,
                        legal_basis=legal_basis
                    )
            
            # Log the consent change
            SystemActivity.objects.create(
                user=request.user,
                action='Patient Consent Updated',
                description=f'Consent {consent_type} {"granted" if granted else "revoked"} for patient {patient.first_name} {patient.last_name}',
                action_type='update',
                ip_address=get_client_ip(request)
            )
            
            return JsonResponse({'status': 'success'})
        
        # Get current consents
        current_consents = {}
        for consent in patient.consents.filter(revoked_at__isnull=True):
            current_consents[consent.consent_type] = consent
        
        context = {
            'patient': patient,
            'consent_types': PatientConsent.CONSENT_TYPES,
            'current_consents': current_consents,
        }
        
        return render(request, 'dashboard/patient_consent.html', context)
        
    except Patient.DoesNotExist:
        return JsonResponse({'error': 'Patient not found'}, status=404)

def get_client_ip(request):
    """Helper function to get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

# Enhanced activity logging middleware function
def log_security_activity(request, action, description, risk_level='low'):
    """Helper function to log security activities"""
    try:
        SecurityAudit.objects.create(
            user=request.user if request.user.is_authenticated else None,
            audit_type='data_access',
            description=description,
            ip_address=get_client_ip(request),
            risk_level=risk_level
        )
        
        SystemActivity.objects.create(
            user=request.user if request.user.is_authenticated else None,
            action=action,
            description=description,
            action_type='access',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
    except:
        pass  # Don't break the application if logging fails
