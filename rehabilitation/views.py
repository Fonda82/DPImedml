from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from datetime import datetime, timedelta, date
from django.utils import timezone
from .models import RehabilitationPlan, RehabilitationSession, RehabilitationAssessment
from patients.models import Patient
from facilities.models import Facility
from accounts.models import UserProfile

# Create your views here.

@login_required
def rehabilitation_list(request):
    # Get filter parameters
    search_query = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', '')
    doctor_filter = request.GET.get('doctor', '')
    facility_filter = request.GET.get('facility', '')
    date_filter = request.GET.get('date_filter', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    session_type_filter = request.GET.get('session_type', '')
    
    # Filter rehabilitation plans based on user role
    user_type = request.user.profile.user_type
    
    if user_type == 'patient':
        # For patients, only show their own rehabilitation plans
        try:
            patient = Patient.objects.get(user=request.user)
            rehabilitation_plans = RehabilitationPlan.objects.filter(patient=patient)
        except Patient.DoesNotExist:
            rehabilitation_plans = RehabilitationPlan.objects.none()
    elif user_type == 'doctor':
        # Special case for demo doctor
        if request.user.username == 'docteur':
            # For demo doctor, show all rehabilitation plans
            rehabilitation_plans = RehabilitationPlan.objects.all()
        else:
            # For regular doctors, show plans they've prescribed
            doctor_profile = request.user.profile
            rehabilitation_plans = RehabilitationPlan.objects.filter(prescribing_doctor=doctor_profile)
    else:
        # For admins and superadmins, show all plans
        rehabilitation_plans = RehabilitationPlan.objects.all()
    
    # Apply search filter
    if search_query:
        search_filter = Q(patient__first_name__icontains=search_query) | \
                       Q(patient__last_name__icontains=search_query) | \
                       Q(patient__patient_id__icontains=search_query) | \
                       Q(diagnosis__icontains=search_query) | \
                       Q(goals__icontains=search_query)
        rehabilitation_plans = rehabilitation_plans.filter(search_filter)
    
    # Apply status filter
    if status_filter:
        rehabilitation_plans = rehabilitation_plans.filter(status=status_filter)
    
    # Apply doctor filter
    if doctor_filter:
        try:
            doctor_id = int(doctor_filter)
            rehabilitation_plans = rehabilitation_plans.filter(prescribing_doctor_id=doctor_id)
        except (ValueError, TypeError):
            pass
    
    # Apply facility filter (by checking sessions)
    if facility_filter:
        try:
            facility_id = int(facility_filter)
            plan_ids = RehabilitationSession.objects.filter(facility_id=facility_id).values_list('rehabilitation_plan_id', flat=True).distinct()
            rehabilitation_plans = rehabilitation_plans.filter(id__in=plan_ids)
        except (ValueError, TypeError):
            pass
    
    # Apply session type filter
    if session_type_filter:
        plan_ids = RehabilitationSession.objects.filter(session_type__icontains=session_type_filter).values_list('rehabilitation_plan_id', flat=True).distinct()
        rehabilitation_plans = rehabilitation_plans.filter(id__in=plan_ids)
    
    # Apply date filters
    if date_filter == 'today':
        today = timezone.now().date()
        rehabilitation_plans = rehabilitation_plans.filter(start_date=today)
    elif date_filter == 'week':
        today = timezone.now().date()
        start_week = today - timedelta(days=today.weekday())
        end_week = start_week + timedelta(days=6)
        rehabilitation_plans = rehabilitation_plans.filter(start_date__range=[start_week, end_week])
    elif date_filter == 'month':
        today = timezone.now().date()
        start_month = today.replace(day=1)
        if today.month == 12:
            end_month = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end_month = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
        rehabilitation_plans = rehabilitation_plans.filter(start_date__range=[start_month, end_month])
    elif date_filter == 'custom' and start_date and end_date:
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
            rehabilitation_plans = rehabilitation_plans.filter(start_date__range=[start_dt, end_dt])
        except ValueError:
            pass
    elif date_filter == 'active':
        # Show plans that are currently active
        today = timezone.now().date()
        rehabilitation_plans = rehabilitation_plans.filter(
            Q(status='active') & 
            Q(start_date__lte=today) & 
            (Q(end_date__gte=today) | Q(end_date__isnull=True))
        )
    
    # Order results
    rehabilitation_plans = rehabilitation_plans.order_by('-start_date')
    
    # Get filter options for the template
    doctors = UserProfile.objects.filter(user_type='doctor').order_by('user__last_name')
    facilities = Facility.objects.all().order_by('name')
    session_types = RehabilitationSession.objects.values_list('session_type', flat=True).distinct()
    session_types = list(set(filter(None, session_types)))
    
    # Handle AJAX requests for real-time filtering
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        plans_data = []
        for plan in rehabilitation_plans:
            # Get session count for this plan
            session_count = RehabilitationSession.objects.filter(rehabilitation_plan=plan).count()
            
            plans_data.append({
                'id': plan.id,
                'patient_name': f"{plan.patient.first_name} {plan.patient.last_name}",
                'patient_id': plan.patient.patient_id,
                'diagnosis': plan.diagnosis or '',
                'goals': plan.goals or '',
                'start_date': plan.start_date.strftime('%Y-%m-%d'),
                'start_date_display': plan.start_date.strftime('%d/%m/%Y'),
                'end_date': plan.end_date.strftime('%Y-%m-%d') if plan.end_date else '',
                'end_date_display': plan.end_date.strftime('%d/%m/%Y') if plan.end_date else 'En cours',
                'status': plan.status,
                'status_display': plan.get_status_display() if hasattr(plan, 'get_status_display') else plan.status,
                'doctor_name': f"Dr. {plan.prescribing_doctor.user.last_name}" if plan.prescribing_doctor else '',
                'session_count': session_count,
                'detail_url': f'/rehabilitation/{plan.id}/',
            })
        
        return JsonResponse({
            'plans': plans_data,
            'total_count': len(plans_data),
            'filters': {
                'search_query': search_query,
                'status_filter': status_filter,
                'doctor_filter': doctor_filter,
                'facility_filter': facility_filter,
                'session_type_filter': session_type_filter,
                'date_filter': date_filter
            }
        })
    
    context = {
        'rehabilitation_plans': rehabilitation_plans,
        'total_count': rehabilitation_plans.count(),
        'doctors': doctors,
        'facilities': facilities,
        'session_types': session_types,
        'filters': {
            'search_query': search_query,
            'status_filter': status_filter,
            'doctor_filter': doctor_filter,
            'facility_filter': facility_filter,
            'session_type_filter': session_type_filter,
            'date_filter': date_filter,
            'start_date': start_date,
            'end_date': end_date
        }
    }
    
    return render(request, 'rehabilitation/list.html', context)

@login_required
def rehabilitation_detail(request, pk):
    # Get actual rehabilitation plan data from database
    plan = get_object_or_404(RehabilitationPlan, pk=pk)
    
    # Check if user has permission to view this plan
    user_type = request.user.profile.user_type
    
    # Special case for demo doctor - allow access to all plans
    if user_type == 'doctor' and request.user.username == 'docteur':
        # Allow access
        pass
    elif user_type == 'patient':
        try:
            patient = Patient.objects.get(user=request.user)
            if plan.patient != patient:
                messages.error(request, "Vous n'avez pas la permission de voir ce plan de réadaptation.")
                return redirect('dashboard:index')
        except Patient.DoesNotExist:
            messages.error(request, "Profil patient non trouvé.")
            return redirect('dashboard:index')
    elif user_type == 'doctor' and plan.prescribing_doctor != request.user.profile:
        # Only allow doctors to see plans they prescribed
        messages.error(request, "Vous n'avez pas la permission de voir ce plan de réadaptation.")
        return redirect('dashboard:index')
    
    # Get sessions for this plan
    sessions = RehabilitationSession.objects.filter(rehabilitation_plan=plan).order_by('session_date')
    
    return render(request, 'rehabilitation/detail.html', {'plan': plan, 'sessions': sessions})

@login_required
def rehabilitation_create(request, patient_id):
    # Get actual patient data from database
    patient = get_object_or_404(Patient, pk=patient_id)
    
    # Check if user has permission to create a plan for this patient
    if request.user.profile.user_type != 'doctor' and request.user.profile.user_type != 'superadmin':
        messages.error(request, "Vous n'avez pas la permission de créer un plan de réadaptation.")
        return redirect('dashboard:index')
    
    if request.method == 'POST':
        # Extract enhanced TDR fields
        diagnosis = request.POST.get('diagnosis', '')
        goals = request.POST.get('goals', '')
        start_date = request.POST.get('start_date') or timezone.now().date()
        end_date = request.POST.get('end_date')
        expected_duration_weeks = int(request.POST.get('expected_duration_weeks', 12))
        family_involvement_score = int(request.POST.get('family_involvement_score', 3))
        
        # Build baseline assessment JSON
        baseline_assessment = {
            'mobility': int(request.POST.get('mobility_score', 3)),
            'communication': int(request.POST.get('communication_score', 3)),
            'cognitive': int(request.POST.get('cognitive_score', 3)),
            'social': int(request.POST.get('social_score', 3)),
            'assessment_date': str(timezone.now().date())
        }
        
        # Build target goals JSON
        target_goals = {
            'mobility': int(request.POST.get('target_mobility', 4)),
            'communication': int(request.POST.get('target_communication', 4)),
            'cognitive': int(request.POST.get('target_cognitive', 4)),
            'social': int(request.POST.get('target_social', 4)),
            'target_date': str(end_date) if end_date else ''
        }
        
        # Create enhanced rehabilitation plan
        new_plan = RehabilitationPlan(
            patient=patient,
            prescribing_doctor=request.user.profile,
            start_date=start_date,
            end_date=end_date,
            diagnosis=diagnosis,
            goals=goals,
            status='active',
            baseline_assessment=baseline_assessment,
            expected_duration_weeks=expected_duration_weeks,
            family_involvement_score=family_involvement_score,
            target_goals=target_goals
        )
        
        new_plan.save()
        
        # Add system activity for enhanced tracking
        try:
            from dashboard.models import SystemActivity
            SystemActivity.objects.create(
                user=request.user,
                action='Plan de réadaptation TDR créé',
                description=f'Plan TDR créé pour {patient.first_name} {patient.last_name} - Durée: {expected_duration_weeks} semaines',
                action_type='create'
            )
        except ImportError:
            pass
        
        messages.success(request, 'Plan de réadaptation créé avec succès!')
        return redirect('rehabilitation:detail', pk=new_plan.pk)
    
    # Get today's date for the form
    today = timezone.now().date()
    
    # Get available rehabilitation types (based on session types in the database)
    rehab_types = set()
    for session in RehabilitationSession.objects.all():
        if session.session_type:
            rehab_types.add(session.session_type)
    
    # If no types found in database, provide some defaults
    if not rehab_types:
        rehab_types = [
            'Kinésithérapie',
            'Orthophonie',
            'Ergothérapie',
            'Stimulation cognitive',
            'Psychomotricité',
        ]
    
    return render(request, 'rehabilitation/create.html', {
        'patient': patient,
        'today': today,
        'rehab_types': [{'id': i+1, 'name': name} for i, name in enumerate(rehab_types)]
    })

@login_required
def rehabilitation_create_select_patient(request):
    """Display a form to select a patient before creating a rehabilitation plan"""
    # Check if user has permission to create a rehabilitation plan
    if request.user.profile.user_type not in ['doctor', 'superadmin']:
        messages.error(request, "Vous n'avez pas la permission de créer un plan de réadaptation.")
        return redirect('dashboard:index')
    
    # If form is submitted, redirect to the create page with the selected patient
    if request.method == 'POST':
        patient_id = request.POST.get('patient')
        if patient_id:
            return redirect('rehabilitation:create', patient_id=patient_id)
        else:
            messages.error(request, "Veuillez sélectionner un patient.")
    
    # Get list of patients for the form
    if request.user.profile.user_type == 'doctor' and request.user.username != 'docteur':
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
    
    return render(request, 'rehabilitation/select_patient.html', {
        'patients': patients
    })

@login_required
def patient_exercises(request):
    """View for patient to see their assigned exercises"""
    # Check if user is a patient
    if request.user.profile.user_type != 'patient':
        messages.error(request, "Cette page est réservée aux patients.")
        return redirect('dashboard:index')
    
    try:
        # Get the patient profile
        patient = Patient.objects.get(user=request.user)
        
        # Get active rehabilitation plan for this patient
        active_plan = RehabilitationPlan.objects.filter(
            patient=patient,
            status='active'
        ).first()
        
        # Get rehabilitation sessions with exercises
        exercises = []
        if active_plan:
            # Get sessions with notes (which might contain exercise instructions)
            sessions = RehabilitationSession.objects.filter(
                rehabilitation_plan=active_plan
            ).exclude(notes__isnull=True).exclude(notes__exact='')
            
            # Extract exercise information from session notes
            for i, session in enumerate(sessions):
                if session.notes:
                    exercises.append({
                        'id': i + 1,
                        'name': f"{session.session_type or 'Exercice'} {i + 1}",
                        'description': session.session_type or "Exercice de réadaptation",
                        'frequency': "Selon prescription",
                        'duration': f"{session.duration_minutes} minutes",
                        'instructions': session.notes
                    })
        
        # If no exercises found, return empty list
        if not exercises:
            exercises = []
            
    except Patient.DoesNotExist:
        exercises = []
    
    return render(request, 'rehabilitation/patient_exercises.html', {
        'exercises': exercises
    })

@login_required
def session_create(request, plan_id):
    """Create a new rehabilitation session for a plan"""
    # Get the rehabilitation plan
    plan = get_object_or_404(RehabilitationPlan, pk=plan_id)
    
    # Check if user has permission to create sessions
    if request.user.profile.user_type not in ['doctor', 'superadmin']:
        messages.error(request, "Vous n'avez pas la permission de créer des séances de réadaptation.")
        return redirect('dashboard:index')
    
    # Get facilities for the form
    facilities = Facility.objects.all().order_by('name')
    
    # Get therapists (doctors) for the form
    therapists = UserProfile.objects.filter(user_type='doctor').order_by('user__last_name')
    
    if request.method == 'POST':
        # Extract form data
        session_date_str = request.POST.get('session_date')
        session_time_str = request.POST.get('session_time')
        facility_id = request.POST.get('facility')
        therapist_id = request.POST.get('therapist')
        session_type = request.POST.get('session_type')
        duration_minutes = request.POST.get('duration_minutes', 60)
        notes = request.POST.get('notes')
        
        # Validate required fields
        if not all([session_date_str, session_time_str, session_type]):
            messages.error(request, "Veuillez remplir tous les champs obligatoires.")
            return render(request, 'rehabilitation/session_create.html', {
                'plan': plan,
                'facilities': facilities,
                'therapists': therapists
            })
        
        try:
            # Combine date and time into a datetime object
            from datetime import datetime
            session_date = datetime.strptime(session_date_str, '%Y-%m-%d').date()
            session_time = datetime.strptime(session_time_str, '%H:%M').time()
            session_datetime = datetime.combine(session_date, session_time)
            session_datetime = timezone.make_aware(session_datetime)
            
            # Get facility and therapist
            facility = None
            if facility_id:
                facility = Facility.objects.get(pk=facility_id)
                
            therapist = None
            if therapist_id:
                therapist = UserProfile.objects.get(pk=therapist_id)
            else:
                therapist = request.user.profile
            
            # Create the session
            session = RehabilitationSession(
                rehabilitation_plan=plan,
                therapist=therapist,
                facility=facility,
                session_date=session_datetime,
                session_type=session_type,
                duration_minutes=int(duration_minutes),
                notes=notes,
                status='planned'
            )
            session.save()
            
            # Add system activity
            try:
                from dashboard.models import SystemActivity
                SystemActivity.objects.create(
                    user=request.user,
                    action='Nouvelle séance de réadaptation créée',
                    description=f'Séance de {session_type} créée pour {plan.patient.first_name} {plan.patient.last_name}',
                    action_type='create'
                )
            except ImportError:
                pass
            
            messages.success(request, "Séance de réadaptation créée avec succès.")
            return redirect('rehabilitation:detail', pk=plan.pk)
            
        except Exception as e:
            messages.error(request, f"Erreur lors de la création de la séance: {str(e)}")
            return render(request, 'rehabilitation/session_create.html', {
                'plan': plan,
                'facilities': facilities,
                'therapists': therapists
            })
    
    # Get common session types
    session_types = [
        'Kinésithérapie',
        'Orthophonie',
        'Ergothérapie',
        'Stimulation cognitive',
        'Psychomotricité',
        'Réadaptation fonctionnelle',
        'Réadaptation neurologique',
        'Thérapie occupationnelle',
    ]
    
    context = {
        'plan': plan,
        'facilities': facilities,
        'therapists': therapists,
        'session_types': session_types,
        'tomorrow': (timezone.now() + timedelta(days=1)).date(),
    }
    
    return render(request, 'rehabilitation/session_create.html', context)
