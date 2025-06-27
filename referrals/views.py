from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Referral, ReferralResponse, ReferralFollowUp
from patients.models import Patient
from facilities.models import Facility
from accounts.models import UserProfile


@login_required
def referral_list(request):
    """List all referrals with filtering and search"""
    user_profile = request.user.profile
    
    # Base queryset based on user role
    if user_profile.user_type == 'superadmin':
        referrals = Referral.objects.all()
    elif user_profile.user_type == 'facility_admin':
        # Show referrals for this facility (both incoming and outgoing)
        facility = user_profile.facility
        referrals = Referral.objects.filter(
            Q(referring_facility=facility) | Q(receiving_facility=facility)
        )
    elif user_profile.user_type == 'doctor':
        # Show referrals sent or received by this doctor
        referrals = Referral.objects.filter(
            Q(referring_doctor=user_profile) | Q(receiving_doctor=user_profile)
        )
    else:
        referrals = Referral.objects.none()
    
    # Search and filters
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    priority_filter = request.GET.get('priority', '')
    facility_filter = request.GET.get('facility', '')
    date_filter = request.GET.get('date_filter', '')
    
    if search_query:
        referrals = referrals.filter(
            Q(referral_id__icontains=search_query) |
            Q(patient__first_name__icontains=search_query) |
            Q(patient__last_name__icontains=search_query) |
            Q(specialty_requested__icontains=search_query) |
            Q(reason_for_referral__icontains=search_query)
        )
    
    if status_filter:
        referrals = referrals.filter(status=status_filter)
    
    if priority_filter:
        referrals = referrals.filter(priority=priority_filter)
    
    if facility_filter:
        referrals = referrals.filter(
            Q(referring_facility_id=facility_filter) | 
            Q(receiving_facility_id=facility_filter)
        )
    
    # Date filtering
    if date_filter:
        today = timezone.now().date()
        if date_filter == 'today':
            referrals = referrals.filter(created_date__date=today)
        elif date_filter == 'week':
            week_start = today - timedelta(days=today.weekday())
            referrals = referrals.filter(created_date__date__gte=week_start)
        elif date_filter == 'month':
            referrals = referrals.filter(
                created_date__year=today.year,
                created_date__month=today.month
            )
    
    referrals = referrals.select_related(
        'patient', 'referring_facility', 'receiving_facility', 
        'referring_doctor', 'receiving_doctor'
    ).order_by('-created_date')
    
    # Get filter options
    facilities = Facility.objects.all()
    
    context = {
        'referrals': referrals,
        'total_count': referrals.count(),
        'facilities': facilities,
        'status_choices': Referral.STATUS_CHOICES,
        'priority_choices': Referral.PRIORITY_CHOICES,
        'filters': {
            'search_query': search_query,
            'status_filter': status_filter,
            'priority_filter': priority_filter,
            'facility_filter': facility_filter,
            'date_filter': date_filter,
        }
    }
    
    return render(request, 'referrals/list.html', context)


@login_required
def referral_detail(request, pk):
    """View referral details"""
    referral = get_object_or_404(Referral, pk=pk)
    
    # Check permissions
    user_profile = request.user.profile
    if (user_profile.user_type == 'doctor' and 
        referral.referring_doctor != user_profile and 
        referral.receiving_doctor != user_profile):
        messages.error(request, "Vous n'avez pas accès à cette référence.")
        return redirect('referrals:list')
    elif (user_profile.user_type == 'facility_admin' and 
          referral.referring_facility != user_profile.facility and 
          referral.receiving_facility != user_profile.facility):
        messages.error(request, "Vous n'avez pas accès à cette référence.")
        return redirect('referrals:list')
    
    # Get related data
    responses = referral.responses.all().order_by('-response_date')
    follow_up = getattr(referral, 'follow_up', None)
    
    context = {
        'referral': referral,
        'responses': responses,
        'follow_up': follow_up,
        'can_respond': (user_profile.user_type in ['doctor', 'facility_admin'] and 
                       referral.receiving_facility == user_profile.facility and 
                       referral.status == 'pending'),
        'can_follow_up': (referral.status == 'completed' and not follow_up)
    }
    
    return render(request, 'referrals/detail.html', context)


@login_required
def referral_create(request):
    """Create new referral"""
    user_profile = request.user.profile
    
    if user_profile.user_type not in ['doctor', 'facility_admin']:
        messages.error(request, "Vous n'avez pas les permissions pour créer une référence.")
        return redirect('referrals:list')
    
    if request.method == 'POST':
        try:
            # Get form data
            patient_id = request.POST.get('patient')
            receiving_facility_id = request.POST.get('receiving_facility')
            referral_type = request.POST.get('referral_type')
            priority = request.POST.get('priority')
            specialty_requested = request.POST.get('specialty_requested')
            reason_for_referral = request.POST.get('reason_for_referral')
            clinical_summary = request.POST.get('clinical_summary')
            current_diagnosis = request.POST.get('current_diagnosis', '')
            current_medications = request.POST.get('current_medications', '')
            specific_questions = request.POST.get('specific_questions', '')
            preferred_date = request.POST.get('preferred_date')
            
            # Validate required fields
            if not all([patient_id, receiving_facility_id, referral_type, priority, 
                       specialty_requested, reason_for_referral, clinical_summary]):
                messages.error(request, "Veuillez remplir tous les champs obligatoires.")
                return render(request, 'referrals/create.html', {
                    'patients': Patient.objects.all(),
                    'facilities': Facility.objects.exclude(id=user_profile.facility.id if user_profile.facility else None),
                    'referral_types': Referral.REFERRAL_TYPE_CHOICES,
                    'priorities': Referral.PRIORITY_CHOICES,
                    'form_data': request.POST
                })
            
            patient = get_object_or_404(Patient, id=patient_id)
            receiving_facility = get_object_or_404(Facility, id=receiving_facility_id)
            
            # Create referral
            referral = Referral.objects.create(
                patient=patient,
                referring_facility=user_profile.facility,
                receiving_facility=receiving_facility,
                referring_doctor=user_profile,
                referral_type=referral_type,
                priority=priority,
                specialty_requested=specialty_requested,
                reason_for_referral=reason_for_referral,
                clinical_summary=clinical_summary,
                current_diagnosis=current_diagnosis,
                current_medications=current_medications,
                specific_questions=specific_questions,
                preferred_date=datetime.strptime(preferred_date, '%Y-%m-%d').date() if preferred_date else None
            )
            
            messages.success(request, f"Référence {referral.referral_id} créée avec succès.")
            return redirect('referrals:detail', pk=referral.pk)
            
        except Exception as e:
            messages.error(request, f"Erreur lors de la création: {str(e)}")
    
    # GET request - show form
    context = {
        'patients': Patient.objects.all(),
        'facilities': Facility.objects.exclude(id=user_profile.facility.id if user_profile.facility else None),
        'referral_types': Referral.REFERRAL_TYPE_CHOICES,
        'priorities': Referral.PRIORITY_CHOICES,
    }
    
    return render(request, 'referrals/create.html', context)


@login_required
def referral_respond(request, pk):
    """Respond to a referral"""
    referral = get_object_or_404(Referral, pk=pk)
    user_profile = request.user.profile
    
    # Check permissions
    if (referral.receiving_facility != user_profile.facility or 
        user_profile.user_type not in ['doctor', 'facility_admin']):
        messages.error(request, "Vous n'avez pas les permissions pour répondre à cette référence.")
        return redirect('referrals:detail', pk=pk)
    
    if referral.status != 'pending':
        messages.warning(request, "Cette référence a déjà reçu une réponse.")
        return redirect('referrals:detail', pk=pk)
    
    if request.method == 'POST':
        response_type = request.POST.get('response_type')
        response_message = request.POST.get('response_message')
        
        # Create response
        response = ReferralResponse.objects.create(
            referral=referral,
            response_type=response_type,
            responding_doctor=user_profile,
            response_message=response_message
        )
        
        # Handle specific response types
        if response_type == 'acceptance':
            proposed_date = request.POST.get('proposed_appointment_date')
            assigned_doctor_id = request.POST.get('assigned_doctor')
            
            if proposed_date:
                response.proposed_appointment_date = datetime.strptime(
                    proposed_date, '%Y-%m-%dT%H:%M'
                )
            if assigned_doctor_id:
                response.assigned_doctor_id = assigned_doctor_id
            
            response.save()
            messages.success(request, "Référence acceptée avec succès.")
            
        elif response_type == 'rejection':
            rejection_reason = request.POST.get('rejection_reason')
            response.rejection_reason = rejection_reason
            response.save()
            messages.success(request, "Référence refusée.")
        
        return redirect('referrals:detail', pk=pk)
    
    # GET - show response form
    doctors = UserProfile.objects.filter(
        facility=user_profile.facility,
        user_type='doctor'
    )
    
    context = {
        'referral': referral,
        'doctors': doctors,
        'response_types': ReferralResponse.RESPONSE_TYPE_CHOICES
    }
    
    return render(request, 'referrals/respond.html', context)


@login_required
def select_patient(request):
    """Select patient for referral (used by create form)"""
    search_query = request.GET.get('search', '')
    
    patients = Patient.objects.all()
    if search_query:
        patients = patients.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(patient_id__icontains=search_query)
        )
    
    patients = patients[:20]  # Limit results
    
    context = {
        'patients': patients,
        'search_query': search_query
    }
    
    return render(request, 'referrals/select_patient.html', context)
