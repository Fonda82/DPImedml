from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from datetime import datetime, timedelta, date
from .models import Appointment
from patients.models import Patient
from accounts.models import UserProfile
from facilities.models import Facility
from django.utils import timezone

# Create your views here.

@login_required
def appointment_list(request):
    # Get filter parameters
    date_filter = request.GET.get('date_filter', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    status_filter = request.GET.get('status', '')
    doctor_filter = request.GET.get('doctor', '')
    facility_filter = request.GET.get('facility', '')
    search_query = request.GET.get('search', '').strip()
    
    # Filter appointments based on user role
    user_type = request.user.profile.user_type
    
    if user_type == 'patient':
        # For patients, only show their own appointments
        try:
            patient = Patient.objects.get(user=request.user)
            appointments = Appointment.objects.filter(patient=patient)
        except Patient.DoesNotExist:
            appointments = Appointment.objects.none()
    elif user_type == 'doctor':
        # Special case for demo doctor - show all appointments
        is_demo_doctor = request.user.username == 'docteur'
        
        if is_demo_doctor:
            # For demo doctor, show all appointments
            appointments = Appointment.objects.all()
        else:
            # For regular doctors, only show appointments where they're the doctor
            doctor_profile = request.user.profile
            appointments = Appointment.objects.filter(doctor=doctor_profile)
    else:
        # For admins and superadmins, show all appointments
        appointments = Appointment.objects.all()
    
    # Apply date filters
    if date_filter == 'today':
        today = timezone.now().date()
        appointments = appointments.filter(appointment_date__date=today)
    elif date_filter == 'week':
        today = timezone.now().date()
        start_week = today - timedelta(days=today.weekday())
        end_week = start_week + timedelta(days=6)
        appointments = appointments.filter(appointment_date__date__range=[start_week, end_week])
    elif date_filter == 'month':
        today = timezone.now().date()
        start_month = today.replace(day=1)
        if today.month == 12:
            end_month = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end_month = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
        appointments = appointments.filter(appointment_date__date__range=[start_month, end_month])
    elif date_filter == 'custom' and start_date and end_date:
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
            appointments = appointments.filter(appointment_date__date__range=[start_dt, end_dt])
        except ValueError:
            pass
    
    # Apply status filter
    if status_filter:
        appointments = appointments.filter(status=status_filter)
    
    # Apply doctor filter
    if doctor_filter:
        try:
            doctor_id = int(doctor_filter)
            appointments = appointments.filter(doctor_id=doctor_id)
        except (ValueError, TypeError):
            pass
    
    # Apply facility filter
    if facility_filter:
        try:
            facility_id = int(facility_filter)
            appointments = appointments.filter(facility_id=facility_id)
        except (ValueError, TypeError):
            pass
    
    # Apply search filter
    if search_query:
        search_filter = Q(patient__first_name__icontains=search_query) | \
                       Q(patient__last_name__icontains=search_query) | \
                       Q(reason__icontains=search_query) | \
                       Q(notes__icontains=search_query)
        appointments = appointments.filter(search_filter)
    
    # Order appointments
    appointments = appointments.order_by('appointment_date')
    
    # Get filter options for the template
    doctors = UserProfile.objects.filter(user_type='doctor').order_by('user__last_name')
    facilities = Facility.objects.all().order_by('name')
    
    # Handle AJAX requests for real-time filtering
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        appointments_data = []
        for appointment in appointments:
            # Format appointment data for JSON response
            appointments_data.append({
                'id': appointment.id,
                'patient_name': f"{appointment.patient.first_name} {appointment.patient.last_name}",
                'patient_id': appointment.patient.patient_id,
                'doctor_name': f"Dr. {appointment.doctor.user.last_name}",
                'facility_name': appointment.facility.name if appointment.facility else '',
                'appointment_date': appointment.appointment_date.strftime('%Y-%m-%d'),
                'appointment_time': appointment.appointment_date.strftime('%H:%M'),
                'reason': appointment.reason,
                'status': appointment.status,
                'status_display': dict(Appointment.STATUS_CHOICES).get(appointment.status, appointment.status) if hasattr(Appointment, 'STATUS_CHOICES') else appointment.status,
                'detail_url': f'/appointments/{appointment.id}/',
                'edit_url': f'/appointments/{appointment.id}/edit/' if hasattr(appointment, 'edit_url') else '#',
            })
        
        return JsonResponse({
            'appointments': appointments_data,
            'total_count': len(appointments_data),
            'filters': {
                'date_filter': date_filter,
                'status_filter': status_filter,
                'doctor_filter': doctor_filter,
                'facility_filter': facility_filter,
                'search_query': search_query
            }
        })
    
    context = {
        'appointments': appointments,
        'total_count': appointments.count(),
        'doctors': doctors,
        'facilities': facilities,
        'filters': {
            'date_filter': date_filter,
            'start_date': start_date,
            'end_date': end_date,
            'status_filter': status_filter,
            'doctor_filter': doctor_filter,
            'facility_filter': facility_filter,
            'search_query': search_query
        }
    }
    
    return render(request, 'appointments/list.html', context)

@login_required
def appointment_detail(request, pk):
    # Get actual appointment data from database
    appointment = get_object_or_404(Appointment, pk=pk)
    
    # Check if user has permission to view this appointment
    user_type = request.user.profile.user_type
    if user_type == 'patient':
        try:
            patient = Patient.objects.get(user=request.user)
            if appointment.patient != patient:
                messages.error(request, "Vous n'avez pas la permission de voir ce rendez-vous.")
                return redirect('dashboard:index')
        except Patient.DoesNotExist:
            messages.error(request, "Profil patient non trouvé.")
            return redirect('dashboard:index')
    elif user_type == 'doctor':
        # Special case for demo doctor - can view any appointment
        is_demo_doctor = request.user.username == 'docteur'
        
        if not is_demo_doctor and appointment.doctor != request.user.profile:
            messages.error(request, "Vous n'avez pas la permission de voir ce rendez-vous.")
            return redirect('dashboard:index')
    
    return render(request, 'appointments/detail.html', {'appointment': appointment})

@login_required
def appointment_create(request):
    """Create a new appointment"""
    # Check if user has permission to create appointments
    user_type = request.user.profile.user_type
    if user_type not in ['doctor', 'facility_admin', 'superadmin']:
        messages.error(request, "Vous n'avez pas la permission de créer des rendez-vous.")
        return redirect('dashboard:index')
    
    if request.method == 'POST':
        # Get form data
        patient_id = request.POST.get('patient')
        doctor_id = request.POST.get('doctor')
        facility_id = request.POST.get('facility')
        date_str = request.POST.get('date')
        time_str = request.POST.get('time')
        reason = request.POST.get('reason')
        notes = request.POST.get('notes')
        
        # Validate required fields
        if not all([patient_id, doctor_id, facility_id, date_str, time_str, reason]):
            messages.error(request, "Veuillez remplir tous les champs obligatoires.")
            return redirect('appointments:create')
        
        try:
            # Get related objects
            patient = Patient.objects.get(id=patient_id)
            doctor = UserProfile.objects.get(id=doctor_id)
            facility = Facility.objects.get(id=facility_id)
            
            # Combine date and time
            from datetime import datetime
            date_time_str = f"{date_str} {time_str}"
            appointment_date = datetime.strptime(date_time_str, '%Y-%m-%d %H:%M')
            
            # Create appointment
            appointment = Appointment(
                patient=patient,
                doctor=doctor,
                facility=facility,
                appointment_date=appointment_date,
                reason=reason,
                notes=notes,
                status='scheduled'
            )
            appointment.save()
            
            messages.success(request, "Rendez-vous créé avec succès.")
            return redirect('appointments:list')
        except (Patient.DoesNotExist, UserProfile.DoesNotExist, Facility.DoesNotExist) as e:
            messages.error(request, f"Erreur: {str(e)}")
            return redirect('appointments:create')
        except Exception as e:
            messages.error(request, f"Une erreur s'est produite: {str(e)}")
            return redirect('appointments:create')
    
    # Get data for form
    patients = Patient.objects.all().order_by('last_name', 'first_name')
    doctors = UserProfile.objects.filter(user_type='doctor').order_by('user__last_name')
    facilities = Facility.objects.all().order_by('name')
    
    context = {
        'patients': patients,
        'doctors': doctors,
        'facilities': facilities
    }
    
    return render(request, 'appointments/create.html', context)
