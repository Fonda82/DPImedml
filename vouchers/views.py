from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from datetime import datetime, timedelta, date
from django.utils import timezone
from .models import Voucher
from patients.models import Patient
from facilities.models import Facility
from accounts.models import UserProfile

@login_required
def voucher_list(request):
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    service_filter = request.GET.get('service', '')
    facility_filter = request.GET.get('facility', '')
    date_filter = request.GET.get('date_filter', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    search_query = request.GET.get('search', '').strip()
    
    # Filter vouchers based on user role
    user_type = request.user.profile.user_type
    
    if user_type == 'patient':
        # For patients, only show their own vouchers
        try:
            patient = Patient.objects.get(user=request.user)
            vouchers = Voucher.objects.filter(patient=patient)
        except Patient.DoesNotExist:
            vouchers = Voucher.objects.none()
    elif user_type == 'doctor':
        # Special case for demo doctor
        if request.user.username == 'docteur':
            # For demo doctor, show all vouchers
            vouchers = Voucher.objects.all()
        else:
            # For regular doctors, show vouchers they've issued
            doctor_profile = request.user.profile
            vouchers = Voucher.objects.filter(issuing_doctor=doctor_profile)
    elif user_type == 'facility_admin':
        # For facility admins, show vouchers for their facility
        facility = request.user.profile.facility
        if facility:
            vouchers = Voucher.objects.filter(Q(issuing_facility=facility) | Q(target_facility=facility))
        else:
            vouchers = Voucher.objects.none()
    else:
        # For superadmins, show all vouchers
        vouchers = Voucher.objects.all()
    
    # Apply status filter
    if status_filter:
        vouchers = vouchers.filter(status=status_filter)
    
    # Apply service type filter
    if service_filter:
        vouchers = vouchers.filter(service_type__icontains=service_filter)
    
    # Apply facility filter
    if facility_filter:
        try:
            facility_id = int(facility_filter)
            vouchers = vouchers.filter(Q(issuing_facility_id=facility_id) | Q(target_facility_id=facility_id))
        except (ValueError, TypeError):
            pass
    
    # Apply date filters
    if date_filter == 'today':
        today = timezone.now().date()
        vouchers = vouchers.filter(issue_date__date=today)
    elif date_filter == 'week':
        today = timezone.now().date()
        start_week = today - timedelta(days=today.weekday())
        end_week = start_week + timedelta(days=6)
        vouchers = vouchers.filter(issue_date__date__range=[start_week, end_week])
    elif date_filter == 'month':
        today = timezone.now().date()
        start_month = today.replace(day=1)
        if today.month == 12:
            end_month = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end_month = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
        vouchers = vouchers.filter(issue_date__date__range=[start_month, end_month])
    elif date_filter == 'custom' and start_date and end_date:
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
            vouchers = vouchers.filter(issue_date__date__range=[start_dt, end_dt])
        except ValueError:
            pass
    elif date_filter == 'expiring':
        # Show vouchers expiring within next 7 days
        today = timezone.now().date()
        expiry_threshold = today + timedelta(days=7)
        vouchers = vouchers.filter(expiry_date__lte=expiry_threshold, status__in=['issued', 'validated'])
    
    # Apply search filter
    if search_query:
        search_filter = Q(voucher_id__icontains=search_query) | \
                       Q(patient__first_name__icontains=search_query) | \
                       Q(patient__last_name__icontains=search_query) | \
                       Q(service_type__icontains=search_query) | \
                       Q(description__icontains=search_query) | \
                       Q(target_facility__name__icontains=search_query)
        vouchers = vouchers.filter(search_filter)
    
    # Order vouchers
    vouchers = vouchers.order_by('-issue_date')
    
    # Get filter options for the template
    facilities = Facility.objects.all().order_by('name')
    service_types = Voucher.objects.values_list('service_type', flat=True).distinct()
    
    # Handle AJAX requests for real-time filtering
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        vouchers_data = []
        for voucher in vouchers:
            vouchers_data.append({
                'id': voucher.id,
                'voucher_id': voucher.voucher_id,
                'patient_name': f"{voucher.patient.first_name} {voucher.patient.last_name}",
                'patient_id': voucher.patient.patient_id,
                'service_type': voucher.service_type,
                'target_facility': voucher.target_facility.name if voucher.target_facility else '',
                'issuing_facility': voucher.issuing_facility.name if voucher.issuing_facility else '',
                'issue_date': voucher.issue_date.strftime('%Y-%m-%d'),
                'expiry_date': voucher.expiry_date.strftime('%Y-%m-%d'),
                'status': voucher.status,
                'status_display': dict(Voucher.STATUS_CHOICES).get(voucher.status, voucher.status) if hasattr(Voucher, 'STATUS_CHOICES') else voucher.status,
                'description': voucher.description or '',
                'detail_url': f'/vouchers/{voucher.id}/',
                'is_expiring': (voucher.expiry_date <= timezone.now().date() + timedelta(days=7)) and voucher.status in ['issued', 'validated'],
                'is_expired': voucher.expiry_date < timezone.now().date() and voucher.status in ['issued', 'validated']
            })
        
        return JsonResponse({
            'vouchers': vouchers_data,
            'total_count': len(vouchers_data),
            'filters': {
                'status_filter': status_filter,
                'service_filter': service_filter,
                'facility_filter': facility_filter,
                'date_filter': date_filter,
                'search_query': search_query
            }
        })
    
    context = {
        'vouchers': vouchers,
        'total_count': vouchers.count(),
        'facilities': facilities,
        'service_types': list(set(filter(None, service_types))),
        'filters': {
            'status_filter': status_filter,
            'service_filter': service_filter,
            'facility_filter': facility_filter,
            'date_filter': date_filter,
            'start_date': start_date,
            'end_date': end_date,
            'search_query': search_query
        }
    }
    
    return render(request, 'vouchers/list.html', context)

@login_required
def voucher_detail(request, pk):
    # Get actual voucher data from database
    voucher = get_object_or_404(Voucher, pk=pk)
    
    # Check if user has permission to view this voucher
    user_type = request.user.profile.user_type
    
    # Special case for demo doctor - allow access to all vouchers
    if user_type == 'doctor' and request.user.username == 'docteur':
        # Allow access
        pass
    elif user_type == 'patient':
        try:
            patient = Patient.objects.get(user=request.user)
            if voucher.patient != patient:
                messages.error(request, "Vous n'avez pas la permission de voir ce bon de prise en charge.")
                return redirect('dashboard:index')
        except Patient.DoesNotExist:
            messages.error(request, "Profil patient non trouvé.")
            return redirect('dashboard:index')
    elif user_type == 'doctor' and voucher.issuing_doctor != request.user.profile:
        # Allow doctors to see vouchers they issued
        if not voucher.issuing_doctor or voucher.issuing_doctor.id != request.user.profile.id:
            messages.error(request, "Vous n'avez pas la permission de voir ce bon de prise en charge.")
            return redirect('dashboard:index')
    elif user_type == 'facility_admin':
        # Allow facility admins to see vouchers for their facility
        facility = request.user.profile.facility
        if not facility or (voucher.issuing_facility != facility and voucher.target_facility != facility):
            messages.error(request, "Vous n'avez pas la permission de voir ce bon de prise en charge.")
            return redirect('dashboard:index')
    
    return render(request, 'vouchers/detail.html', {'voucher': voucher})

@login_required
def voucher_create(request):
    """Create a new voucher."""
    # Check if user has permission to create vouchers
    user_type = request.user.profile.user_type
    if user_type not in ['doctor', 'facility_admin', 'superadmin']:
        messages.error(request, "Vous n'avez pas la permission de créer des bons de prise en charge.")
        return redirect('dashboard:index')
    
    # Get list of patients for the form
    if user_type == 'doctor' and request.user.username != 'docteur':
        # For regular doctors, show patients under their care
        doctor_profile = request.user.profile
        try:
            # Try to get patients with medical records linked to this doctor
            patients_with_records = Patient.objects.filter(medicalrecord__doctor=doctor_profile).distinct()
            
            # If no patients found, show all patients
            if not patients_with_records.exists():
                patients = Patient.objects.all().order_by('last_name', 'first_name')
            else:
                patients = patients_with_records
        except Exception:
            # Fallback to all patients if there's an error
            patients = Patient.objects.all().order_by('last_name', 'first_name')
    else:
        # For demo doctor, admins, and superadmins, show all patients
        patients = Patient.objects.all().order_by('last_name', 'first_name')
    
    # Get list of facilities for the form
    facilities = Facility.objects.all().order_by('name')
    
    if request.method == 'POST':
        # Extract form data
        patient_id = request.POST.get('patient')
        target_facility_id = request.POST.get('target_facility')
        service_type = request.POST.get('service_type')
        description = request.POST.get('description')
        expiry_days = int(request.POST.get('expiry_days', 90))
        
        # Validate required fields
        if not all([patient_id, target_facility_id, service_type]):
            messages.error(request, "Veuillez remplir tous les champs obligatoires.")
            return render(request, 'vouchers/create.html', {
                'patients': patients,
                'facilities': facilities
            })
        
        try:
            # Get patient and facility objects
            patient = Patient.objects.get(pk=patient_id)
            target_facility = Facility.objects.get(pk=target_facility_id)
            
            # Get issuing doctor and facility
            issuing_doctor = request.user.profile
            
            # For facility admin or superadmin, use the specified facility
            if user_type in ['facility_admin', 'superadmin']:
                issuing_facility_id = request.POST.get('issuing_facility')
                if issuing_facility_id:
                    issuing_facility = Facility.objects.get(pk=issuing_facility_id)
                else:
                    # Use user's facility or first available facility
                    issuing_facility = getattr(request.user.profile, 'facility', None) or facilities.first()
            else:
                # For doctors, use their facility
                issuing_facility = getattr(request.user.profile, 'facility', None) or facilities.first()
            
            # Calculate expiry date
            from datetime import timedelta
            expiry_date = timezone.now().date() + timedelta(days=expiry_days)
            
            # Create voucher
            voucher = Voucher(
                patient=patient,
                issuing_doctor=issuing_doctor,
                issuing_facility=issuing_facility,
                target_facility=target_facility,
                service_type=service_type,
                description=description,
                expiry_date=expiry_date,
                status='issued'
            )
            voucher.save()
            
            # Add system activity
            from dashboard.models import SystemActivity
            SystemActivity.objects.create(
                user=request.user,
                action='Nouveau bon créé',
                description=f'Bon de prise en charge créé pour {patient.first_name} {patient.last_name}',
                action_type='create'
            )
            
            messages.success(request, f"Bon de prise en charge créé avec succès pour {patient.first_name} {patient.last_name}.")
            return redirect('vouchers:detail', pk=voucher.pk)
            
        except (Patient.DoesNotExist, Facility.DoesNotExist) as e:
            messages.error(request, f"Erreur lors de la création du bon: {str(e)}")
            return render(request, 'vouchers/create.html', {
                'patients': patients,
                'facilities': facilities
            })
    
    context = {
        'patients': patients,
        'facilities': facilities
    }
    
    return render(request, 'vouchers/create.html', context)
