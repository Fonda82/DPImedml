from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.db.models import Q
from .models import Patient, MedicalRecord, Document, ICD10Code, VitalSigns
from django.utils import timezone
from accounts.models import UserProfile
from facilities.models import Facility
import json

# Create your views here.

@login_required
def patient_list(request):
    # Get search query from request
    search_query = request.GET.get('search', '').strip()
    
    # Filter patients based on user role
    user_type = request.user.profile.user_type
    
    if user_type == 'patient':
        # For patients, only show their own record
        try:
            patient = Patient.objects.get(user=request.user)
            patients = [patient]
        except Patient.DoesNotExist:
            patients = []
    elif user_type == 'doctor':
        # Special case for demo doctor
        if request.user.username == 'docteur':
            # For demo doctor, show all patients
            patients = Patient.objects.all()
        else:
            # For regular doctors, show patients under their care
            doctor_profile = request.user.profile
            patients = Patient.objects.filter(
                medicalrecord__doctor=doctor_profile
            ).distinct()
    else:
        # For admins and superadmins, show all patients
        patients = Patient.objects.all()
    
    # Apply search filter if search query exists
    if search_query:
        search_filter = Q(first_name__icontains=search_query) | \
                       Q(last_name__icontains=search_query) | \
                       Q(patient_id__icontains=search_query) | \
                       Q(phone_number__icontains=search_query) | \
                       Q(city__icontains=search_query)
        
        if user_type == 'patient':
            # For patients, filter their single record only
            patients = [p for p in patients if search_query.lower() in f"{p.first_name} {p.last_name} {p.patient_id} {p.phone_number or ''} {p.city or ''}".lower()]
        else:
            # For other roles, use database filtering
            patients = patients.filter(search_filter)
    
    # Order results
    if user_type != 'patient':
        patients = patients.order_by('last_name', 'first_name')
    
    # Handle AJAX requests for real-time search
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        patients_data = []
        for patient in patients:
            # Calculate age
            age = None
            if patient.date_of_birth:
                from datetime import date
                today = date.today()
                age = today.year - patient.date_of_birth.year - ((today.month, today.day) < (patient.date_of_birth.month, patient.date_of_birth.day))
            
            patients_data.append({
                'id': patient.id,
                'patient_id': patient.patient_id,
                'first_name': patient.first_name,
                'last_name': patient.last_name,
                'age': age,
                'phone_number': patient.phone_number or '',
                'city': patient.city or '',
                'gender': patient.get_gender_display() if hasattr(patient, 'get_gender_display') else patient.gender,
                'detail_url': f'/patients/{patient.id}/',
                'edit_url': f'/patients/{patient.id}/edit/',
            })
        
        return JsonResponse({
            'patients': patients_data,
            'total_count': len(patients_data),
            'search_query': search_query
        })
    
    context = {
        'patients': patients,
        'search_query': search_query,
        'total_count': len(patients) if user_type == 'patient' else patients.count()
    }
    
    return render(request, 'patients/list.html', context)

@login_required
def patient_detail(request, pk):
    # Get actual patient data from database
    patient = get_object_or_404(Patient, pk=pk)
    
    # Check if user has permission to view this patient
    user_type = request.user.profile.user_type
    
    # Special case for demo doctor - allow access to all patients
    if user_type == 'doctor' and request.user.username == 'docteur':
        # Allow access
        pass
    elif user_type == 'patient' and patient.user != request.user:
        messages.error(request, "Vous n'avez pas la permission de voir ce dossier patient.")
        return redirect('dashboard:index')
    
    return render(request, 'patients/detail.html', {'patient': patient})

@login_required
def medical_profile(request, pk):
    """
    Display comprehensive medical profile including all medical records,
    diagnostics, prescriptions, and treatment history.
    This view is separate from the dashboard overview.
    """
    # Get actual patient data from database
    patient = get_object_or_404(Patient, pk=pk)
    
    # Check if user has permission to view this patient
    user_type = request.user.profile.user_type
    
    # Special case for demo doctor - allow access to all patients
    if user_type == 'doctor' and request.user.username == 'docteur':
        # Allow access
        pass
    elif user_type == 'patient' and patient.user != request.user:
        messages.error(request, "Vous n'avez pas la permission de voir ce dossier médical.")
        return redirect('dashboard:index')
    
    # Get medical records for this patient
    medical_history = MedicalRecord.objects.filter(patient=patient).order_by('-date')
    
    # Get prescriptions (if prescription model exists)
    prescriptions = []
    try:
        from prescriptions.models import Prescription
        prescriptions = Prescription.objects.filter(patient=patient).order_by('-prescribed_date')
    except ImportError:
        pass
    
    # Get rehabilitation sessions
    rehabilitation_sessions = []
    try:
        from rehabilitation.models import RehabilitationSession, RehabilitationPlan
        rehab_plans = RehabilitationPlan.objects.filter(patient=patient)
        for plan in rehab_plans:
            sessions = RehabilitationSession.objects.filter(rehabilitation_plan=plan)
            rehabilitation_sessions.extend(sessions)
    except ImportError:
        pass
    
    context = {
        'patient': patient,
        'medical_history': medical_history,
        'prescriptions': prescriptions,
        'rehabilitation_sessions': rehabilitation_sessions,
    }
    
    return render(request, 'patients/medical_profile.html', context)

@login_required
def patient_create(request):
    """Create a new patient."""
    # Check if user has permission to create patients
    user_type = request.user.profile.user_type
    if user_type not in ['doctor', 'facility_admin', 'superadmin']:
        messages.error(request, "Vous n'avez pas la permission de créer des patients.")
        return redirect('dashboard:index')
    
    if request.method == 'POST':
        # Extract form data
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        date_of_birth = request.POST.get('date_of_birth')
        gender = request.POST.get('gender')
        phone_number = request.POST.get('phone_number')
        email = request.POST.get('email')
        address = request.POST.get('address')
        city = request.POST.get('city', 'Bamako')
        region = request.POST.get('region')
        guardian_name = request.POST.get('guardian_name')
        guardian_relationship = request.POST.get('guardian_relationship')
        guardian_phone = request.POST.get('guardian_phone')
        create_user = request.POST.get('create_user') == 'on'
        
        # Validate required fields
        if not all([first_name, last_name, date_of_birth, gender]):
            messages.error(request, "Veuillez remplir tous les champs obligatoires.")
            return render(request, 'patients/create.html')
        
        # Create patient
        patient = Patient(
            first_name=first_name,
            last_name=last_name,
            date_of_birth=date_of_birth,
            gender=gender,
            phone_number=phone_number,
            email=email,
            address=address,
            city=city,
            region=region,
            guardian_name=guardian_name,
            guardian_relationship=guardian_relationship,
            guardian_phone=guardian_phone
        )
        # Patient ID will be generated automatically in the model's save method
        
        # Create user account if requested
        if create_user:
            username = request.POST.get('username')
            password = request.POST.get('password')
            
            if not username or not password:
                messages.error(request, "Nom d'utilisateur et mot de passe requis pour créer un compte.")
                return render(request, 'patients/create.html')
            
            # Check if username already exists
            if User.objects.filter(username=username).exists():
                messages.error(request, "Ce nom d'utilisateur existe déjà.")
                return render(request, 'patients/create.html')
            
            # Create user
            from django.contrib.auth.models import User
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            # Create patient profile
            from accounts.models import UserProfile
            profile = UserProfile.objects.create(
                user=user,
                user_type='patient'
            )
            
            # Link user to patient
            patient.user = user
        
        # Save patient
        patient.save()
        
        # Add system activity
        from dashboard.models import SystemActivity
        SystemActivity.objects.create(
            user=request.user,
            action='Nouveau patient créé',
            description=f'Patient {first_name} {last_name} créé par {request.user.username}',
            action_type='create'
        )
        
        messages.success(request, f"Patient {first_name} {last_name} créé avec succès.")
        return redirect('patients:detail', pk=patient.pk)
    
    return render(request, 'patients/create.html')

@login_required
def patient_edit(request, pk):
    """Edit patient information."""
    # Get actual patient data from database
    patient = get_object_or_404(Patient, pk=pk)
    
    # Check if user has permission to edit this patient
    user_type = request.user.profile.user_type
    if user_type == 'patient' and patient.user != request.user:
        messages.error(request, "Vous n'avez pas la permission de modifier ce dossier patient.")
        return redirect('dashboard:index')
    
    if request.method == 'POST':
        # Update patient information
        patient.first_name = request.POST.get('first_name', patient.first_name)
        patient.last_name = request.POST.get('last_name', patient.last_name)
        patient.date_of_birth = request.POST.get('date_of_birth', patient.date_of_birth)
        patient.gender = request.POST.get('gender', patient.gender)
        patient.address = request.POST.get('address', patient.address)
        patient.phone_number = request.POST.get('phone_number', patient.phone_number)
        patient.email = request.POST.get('email', patient.email)
        patient.city = request.POST.get('city', patient.city)
        patient.region = request.POST.get('region', patient.region)
        patient.guardian_name = request.POST.get('guardian_name', patient.guardian_name)
        patient.guardian_relationship = request.POST.get('guardian_relationship', patient.guardian_relationship)
        patient.guardian_phone = request.POST.get('guardian_phone', patient.guardian_phone)
        patient.updated_at = timezone.now()
        patient.save()
        
        # Add system activity
        try:
            from dashboard.models import SystemActivity
            SystemActivity.objects.create(
                user=request.user,
                action='Patient modifié',
                description=f'Patient {patient.first_name} {patient.last_name} modifié par {request.user.username}',
                action_type='update'
            )
        except ImportError:
            pass
            
        messages.success(request, "Informations du patient mises à jour avec succès.")
        return redirect('patients:detail', pk=pk)
    
    context = {'patient': patient}
    return render(request, 'patients/edit.html', context)

@login_required
def medical_history(request, pk):
    """Display medical history for a patient with smart filtering."""
    # Get actual patient data from database
    patient = get_object_or_404(Patient, pk=pk)
    
    # Get filter parameters
    search_query = request.GET.get('search', '').strip()
    doctor_filter = request.GET.get('doctor', '')
    facility_filter = request.GET.get('facility', '')
    date_filter = request.GET.get('date_filter', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    
    # Check if user has permission to view this patient
    user_type = request.user.profile.user_type
    
    # Special case for demo doctor - allow access to all patients
    if user_type == 'doctor' and request.user.username == 'docteur':
        # Allow access
        pass
    elif user_type == 'patient' and patient.user != request.user:
        messages.error(request, "Vous n'avez pas la permission de voir ce dossier médical.")
        return redirect('dashboard:index')
    
    # Get medical records for this patient
    medical_records = MedicalRecord.objects.filter(patient=patient)
    
    # Apply search filter
    if search_query:
        search_filter = Q(diagnosis__icontains=search_query) | \
                       Q(description__icontains=search_query) | \
                       Q(recommendations__icontains=search_query)
        medical_records = medical_records.filter(search_filter)
    
    # Apply doctor filter
    if doctor_filter:
        try:
            doctor_id = int(doctor_filter)
            medical_records = medical_records.filter(doctor_id=doctor_id)
        except (ValueError, TypeError):
            pass
    
    # Apply facility filter
    if facility_filter:
        try:
            facility_id = int(facility_filter)
            medical_records = medical_records.filter(facility_id=facility_id)
        except (ValueError, TypeError):
            pass
    
    # Apply date filters
    if date_filter == 'today':
        from datetime import date
        today = date.today()
        medical_records = medical_records.filter(date__date=today)
    elif date_filter == 'week':
        from datetime import date, timedelta
        today = date.today()
        start_week = today - timedelta(days=today.weekday())
        end_week = start_week + timedelta(days=6)
        medical_records = medical_records.filter(date__date__range=[start_week, end_week])
    elif date_filter == 'month':
        from datetime import date, timedelta
        today = date.today()
        start_month = today.replace(day=1)
        if today.month == 12:
            end_month = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end_month = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
        medical_records = medical_records.filter(date__date__range=[start_month, end_month])
    elif date_filter == 'custom' and start_date and end_date:
        try:
            from datetime import datetime
            start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
            medical_records = medical_records.filter(date__date__range=[start_dt, end_dt])
        except ValueError:
            pass
    
    # Order results
    medical_records = medical_records.order_by('-date')
    
    # Get filter options for the template
    from accounts.models import UserProfile
    from facilities.models import Facility
    doctors = UserProfile.objects.filter(user_type='doctor').order_by('user__last_name')
    facilities = Facility.objects.all().order_by('name')
    
    # Handle AJAX requests for real-time filtering
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        records_data = []
        for record in medical_records:
            records_data.append({
                'id': record.id,
                'date': record.date.strftime('%Y-%m-%d %H:%M') if record.date else '',
                'date_display': record.date.strftime('%d/%m/%Y') if record.date else '',
                'diagnosis': record.diagnosis or '',
                'description': record.description or '',
                'recommendations': record.recommendations or '',
                'doctor_name': f"Dr. {record.doctor.user.last_name}" if record.doctor else '',
                'facility_name': record.facility.name if record.facility else '',
                'detail_url': f'/patients/medical-record/{record.id}/',
            })
        
        return JsonResponse({
            'records': records_data,
            'total_count': len(records_data),
            'filters': {
                'search_query': search_query,
                'doctor_filter': doctor_filter,
                'facility_filter': facility_filter,
                'date_filter': date_filter
            }
        })
    
    context = {
        'patient': patient,
        'medical_records': medical_records,
        'total_count': medical_records.count(),
        'doctors': doctors,
        'facilities': facilities,
        'filters': {
            'search_query': search_query,
            'doctor_filter': doctor_filter,
            'facility_filter': facility_filter,
            'date_filter': date_filter,
            'start_date': start_date,
            'end_date': end_date
        }
    }
    
    return render(request, 'patients/medical_history.html', context)

@login_required
def medical_record(request, pk):
    """Display details of a specific medical record."""
    # Get actual medical record data from database
    record = get_object_or_404(MedicalRecord, pk=pk)
    
    # Check if user has permission to view this record
    user_type = request.user.profile.user_type
    
    # Special case for demo doctor - allow access to all records
    if user_type == 'doctor' and request.user.username == 'docteur':
        # Allow access
        pass
    elif user_type == 'patient' and record.patient.user != request.user:
        messages.error(request, "Vous n'avez pas la permission de voir ce dossier médical.")
        return redirect('dashboard:index')
    
    return render(request, 'patients/medical_record.html', {'record': record})

@login_required
def patient_documents(request, pk):
    """Display patient's medical documents."""
    # Get actual patient data from database
    patient = get_object_or_404(Patient, pk=pk)
    
    # Check if user has permission to view this patient
    user_type = request.user.profile.user_type
    
    # Special case for demo doctor - allow access to all patients
    if user_type == 'doctor' and request.user.username == 'docteur':
        # Allow access
        pass
    elif user_type == 'patient' and patient.user != request.user:
        messages.error(request, "Vous n'avez pas la permission de voir ces documents.")
        return redirect('dashboard:index')
    
    # Get patient documents
    documents = Document.objects.filter(patient=patient).order_by('-upload_date')
    
    return render(request, 'patients/documents.html', {'patient': patient, 'documents': documents})

@login_required
def add_document(request, pk):
    """Add a new document to a patient's record."""
    patient = get_object_or_404(Patient, pk=pk)
    
    # Check if user has permission to add documents for this patient
    user_type = request.user.profile.user_type
    
    # Special case for demo doctor - allow access to all patients
    if user_type == 'doctor' and request.user.username == 'docteur':
        # Allow access
        pass
    elif user_type != 'doctor' and user_type != 'facility_admin' and user_type != 'superadmin':
        messages.error(request, "Vous n'avez pas la permission d'ajouter des documents.")
        return redirect('dashboard:index')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        category = request.POST.get('category')
        description = request.POST.get('description')
        document_date = request.POST.get('date')
        document_file = request.FILES.get('document')
        
        if title and document_file:
            document = Document(
                patient=patient,
                title=title,
                category=category,
                description=description,
                file=document_file,
                uploaded_by=request.user.profile,
                document_date=document_date if document_date else timezone.now().date()
            )
            document.save()
            messages.success(request, "Document ajouté avec succès.")
            return redirect('patients:documents', pk=patient.pk)
        else:
            messages.error(request, "Veuillez fournir un titre et un fichier.")
    
    return redirect('patients:documents', pk=patient.pk)

@login_required
def icd10_search(request):
    """
    AJAX endpoint for searching ICD-10 codes with autocompletion
    """
    query = request.GET.get('q', '').strip()
    category = request.GET.get('category', '')
    pediatric_only = request.GET.get('pediatric', 'false').lower() == 'true'
    disability_only = request.GET.get('disability', 'false').lower() == 'true'
    mali_common = request.GET.get('mali', 'false').lower() == 'true'
    
    if len(query) < 2:
        return JsonResponse({'codes': []})
    
    # Build search query
    search_filter = Q(code__icontains=query) | Q(title__icontains=query) | Q(description__icontains=query)
    
    icd10_codes = ICD10Code.objects.filter(search_filter)
    
    # Apply filters
    if category:
        icd10_codes = icd10_codes.filter(category=category)
    if pediatric_only:
        icd10_codes = icd10_codes.filter(is_pediatric_relevant=True)
    if disability_only:
        icd10_codes = icd10_codes.filter(is_disability_related=True)
    if mali_common:
        icd10_codes = icd10_codes.filter(is_common_in_mali=True)
    
    # Limit results for performance
    icd10_codes = icd10_codes.order_by('code')[:20]
    
    codes_data = []
    for code in icd10_codes:
        codes_data.append({
            'id': code.id,
            'code': code.code,
            'title': code.title,
            'description': code.description,
            'category': code.get_category_display(),
            'category_code': code.category,
            'is_pediatric': code.is_pediatric_relevant,
            'is_disability': code.is_disability_related,
            'is_mali_common': code.is_common_in_mali,
            'display': f"{code.code} - {code.title}"
        })
    
    return JsonResponse({'codes': codes_data})

@login_required
def medical_record_create(request, patient_id):
    """
    Create a new medical record with ICD-10 professional diagnostic coding
    """
    patient = get_object_or_404(Patient, id=patient_id)
    
    # Check permissions
    if request.user.profile.user_type not in ['doctor', 'superadmin']:
        messages.error(request, "Vous n'avez pas la permission de créer des dossiers médicaux.")
        return redirect('patients:detail', pk=patient_id)
    
    if request.method == 'POST':
        try:
            # Create medical record
            medical_record = MedicalRecord(
                patient=patient,
                doctor=request.user.profile,
                facility=request.user.profile.facility if hasattr(request.user.profile, 'facility') else None,
                date=timezone.now(),
                chief_complaint=request.POST.get('chief_complaint', ''),
                present_illness=request.POST.get('present_illness', ''),
                physical_examination=request.POST.get('physical_examination', ''),
                clinical_notes=request.POST.get('clinical_notes', ''),
                treatment_plan=request.POST.get('treatment_plan', ''),
                recommendations=request.POST.get('recommendations', ''),
                follow_up_instructions=request.POST.get('follow_up_instructions', ''),
                description=request.POST.get('description', ''),  # Legacy field
            )
            
            # Handle ICD-10 primary diagnosis
            primary_diagnosis_id = request.POST.get('primary_diagnosis_icd10')
            if primary_diagnosis_id:
                try:
                    primary_diagnosis = ICD10Code.objects.get(id=primary_diagnosis_id)
                    medical_record.primary_diagnosis_icd10 = primary_diagnosis
                except ICD10Code.DoesNotExist:
                    messages.warning(request, "Code ICD-10 principal introuvable.")
            
            # Legacy diagnosis fallback
            if not primary_diagnosis_id:
                medical_record.diagnosis = request.POST.get('diagnosis', '')
            
            medical_record.save()
            
            # Handle secondary diagnoses
            secondary_diagnosis_ids = request.POST.getlist('secondary_diagnoses_icd10')
            if secondary_diagnosis_ids:
                secondary_diagnoses = ICD10Code.objects.filter(id__in=secondary_diagnosis_ids)
                medical_record.secondary_diagnoses_icd10.set(secondary_diagnoses)
            
            # Create vital signs if provided
            if any([request.POST.get('temperature'), request.POST.get('heart_rate'), 
                    request.POST.get('height'), request.POST.get('weight')]):
                
                vital_signs = VitalSigns(
                    medical_record=medical_record,
                    temperature=request.POST.get('temperature') or None,
                    heart_rate=request.POST.get('heart_rate') or None,
                    respiratory_rate=request.POST.get('respiratory_rate') or None,
                    systolic_bp=request.POST.get('systolic_bp') or None,
                    diastolic_bp=request.POST.get('diastolic_bp') or None,
                    oxygen_saturation=request.POST.get('oxygen_saturation') or None,
                    height=request.POST.get('height') or None,
                    weight=request.POST.get('weight') or None,
                    head_circumference=request.POST.get('head_circumference') or None,
                    developmental_milestones_appropriate=request.POST.get('developmental_milestones') == 'on',
                    notes=request.POST.get('vital_signs_notes', '')
                )
                vital_signs.save()
            
            messages.success(request, "Dossier médical créé avec succès!")
            return redirect('patients:medical_record', record_id=medical_record.id)
            
        except Exception as e:
            messages.error(request, f"Erreur lors de la création du dossier: {str(e)}")
            return redirect('patients:detail', pk=patient_id)
    
    # GET request - show form
    context = {
        'patient': patient,
        'icd10_categories': ICD10Code.CATEGORY_CHOICES,
        'today': timezone.now().date(),
    }
    
    return render(request, 'patients/medical_record_create.html', context)

@login_required
def vital_signs_dashboard(request, pk):
    """
    Comprehensive vital signs dashboard with trends, alerts, and growth charts
    for pediatric patients (0-14 years)
    """
    patient = get_object_or_404(Patient, pk=pk)
    
    # Check permissions
    user_type = request.user.profile.user_type
    if user_type == 'doctor' and request.user.username == 'docteur':
        pass  # Demo doctor access
    elif user_type == 'patient' and patient.user != request.user:
        messages.error(request, "Vous n'avez pas la permission de voir ces signes vitaux.")
        return redirect('dashboard:index')
    
    # Get all vital signs for this patient
    vital_signs_records = VitalSigns.objects.filter(
        medical_record__patient=patient
    ).select_related('medical_record').order_by('-medical_record__date')
    
    # Calculate patient age
    patient_age = None
    if patient.date_of_birth:
        from datetime import date
        today = date.today()
        patient_age = today.year - patient.date_of_birth.year - (
            (today.month, today.day) < (patient.date_of_birth.month, patient.date_of_birth.day)
        )
    
    # Get latest vital signs
    latest_vitals = vital_signs_records.first() if vital_signs_records.exists() else None
    
    # Generate alerts for abnormal values (pediatric ranges)
    alerts = []
    if latest_vitals:
        alerts = generate_vital_signs_alerts(latest_vitals, patient_age)
    
    # Calculate growth percentiles and nutritional status trends
    growth_data = calculate_growth_trends(vital_signs_records, patient_age)
    
    # Prepare chart data for frontend
    chart_data = prepare_vital_signs_chart_data(vital_signs_records)
    
    context = {
        'patient': patient,
        'patient_age': patient_age,
        'vital_signs_records': vital_signs_records[:10],  # Latest 10 records
        'latest_vitals': latest_vitals,
        'alerts': alerts,
        'growth_data': growth_data,
        'chart_data': chart_data,
        'total_records': vital_signs_records.count(),
    }
    
    return render(request, 'patients/vital_signs_dashboard.html', context)

@login_required
def vital_signs_trends(request, pk):
    """
    API endpoint for vital signs trends data (AJAX)
    Returns JSON data for charts and visualizations
    """
    patient = get_object_or_404(Patient, pk=pk)
    
    # Check permissions
    user_type = request.user.profile.user_type
    if user_type == 'doctor' and request.user.username == 'docteur':
        pass  # Demo doctor access
    elif user_type == 'patient' and patient.user != request.user:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    # Get time range filter
    time_range = request.GET.get('range', '6months')  # 6months, 1year, 2years, all
    
    # Filter vital signs based on time range
    vital_signs = VitalSigns.objects.filter(
        medical_record__patient=patient
    ).select_related('medical_record')
    
    if time_range == '6months':
        from datetime import date, timedelta
        cutoff_date = date.today() - timedelta(days=180)
        vital_signs = vital_signs.filter(medical_record__date__date__gte=cutoff_date)
    elif time_range == '1year':
        from datetime import date, timedelta
        cutoff_date = date.today() - timedelta(days=365)
        vital_signs = vital_signs.filter(medical_record__date__date__gte=cutoff_date)
    elif time_range == '2years':
        from datetime import date, timedelta
        cutoff_date = date.today() - timedelta(days=730)
        vital_signs = vital_signs.filter(medical_record__date__date__gte=cutoff_date)
    
    vital_signs = vital_signs.order_by('medical_record__date')
    
    # Prepare data for different chart types
    trends_data = {
        'growth': [],
        'vitals': [],
        'bmi': [],
        'development': []
    }
    
    for vs in vital_signs:
        record_date = vs.medical_record.date.strftime('%Y-%m-%d') if vs.medical_record.date else None
        
        # Growth data (height, weight, head circumference)
        if vs.height or vs.weight or vs.head_circumference:
            trends_data['growth'].append({
                'date': record_date,
                'height': float(vs.height) if vs.height else None,
                'weight': float(vs.weight) if vs.weight else None,
                'head_circumference': float(vs.head_circumference) if vs.head_circumference else None,
                'bmi': float(vs.bmi) if vs.bmi else None,
            })
        
        # Vital signs data (temperature, heart rate, etc.)
        if any([vs.temperature, vs.heart_rate, vs.respiratory_rate, vs.systolic_bp]):
            trends_data['vitals'].append({
                'date': record_date,
                'temperature': float(vs.temperature) if vs.temperature else None,
                'heart_rate': vs.heart_rate,
                'respiratory_rate': vs.respiratory_rate,
                'systolic_bp': vs.systolic_bp,
                'diastolic_bp': vs.diastolic_bp,
                'oxygen_saturation': vs.oxygen_saturation,
            })
        
        # BMI and nutritional status
        if vs.bmi:
            trends_data['bmi'].append({
                'date': record_date,
                'bmi': float(vs.bmi),
                'nutritional_status': vs.nutritional_status,
                'percentile': vs.bmi_percentile,
            })
    
    return JsonResponse(trends_data)

@login_required
def growth_chart(request, pk):
    """
    Generate growth chart data with WHO percentiles for pediatric patients
    """
    patient = get_object_or_404(Patient, pk=pk)
    
    # Check permissions
    user_type = request.user.profile.user_type
    if user_type == 'doctor' and request.user.username == 'docteur':
        pass  # Demo doctor access
    elif user_type == 'patient' and patient.user != request.user:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    # Get patient's growth data
    vital_signs = VitalSigns.objects.filter(
        medical_record__patient=patient
    ).select_related('medical_record').order_by('medical_record__date')
    
    # Calculate patient age for each record
    patient_birth = patient.date_of_birth
    if not patient_birth:
        return JsonResponse({'error': 'Date of birth required for growth charts'}, status=400)
    
    growth_data = []
    for vs in vital_signs:
        if vs.medical_record.date and (vs.height or vs.weight):
            # Calculate age in months at time of measurement
            record_date = vs.medical_record.date.date()
            age_days = (record_date - patient_birth).days
            age_months = age_days / 30.44  # Average days per month
            
            growth_data.append({
                'age_months': round(age_months, 1),
                'height': float(vs.height) if vs.height else None,
                'weight': float(vs.weight) if vs.weight else None,
                'head_circumference': float(vs.head_circumference) if vs.head_circumference else None,
                'date': record_date.strftime('%Y-%m-%d'),
            })
    
    # Add WHO percentile reference data (simplified - in production, use WHO tables)
    who_percentiles = generate_who_reference_data(patient.gender, max(168, max([d['age_months'] for d in growth_data]) if growth_data else 168))
    
    return JsonResponse({
        'patient_data': growth_data,
        'who_percentiles': who_percentiles,
        'patient_gender': patient.gender,
        'current_age_months': age_months if growth_data else 0,
    })

@login_required
def vital_signs_api(request, pk):
    """
    API endpoint for vital signs data (used by dashboard widgets)
    """
    patient = get_object_or_404(Patient, pk=pk)
    
    # Check permissions
    user_type = request.user.profile.user_type
    if user_type == 'doctor' and request.user.username == 'docteur':
        pass  # Demo doctor access
    elif user_type == 'patient' and patient.user != request.user:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    # Get latest vital signs
    latest_vitals = VitalSigns.objects.filter(
        medical_record__patient=patient
    ).select_related('medical_record').order_by('-medical_record__date').first()
    
    if not latest_vitals:
        return JsonResponse({'error': 'No vital signs data found'}, status=404)
    
    # Calculate patient age
    patient_age = None
    if patient.date_of_birth:
        from datetime import date
        today = date.today()
        patient_age = today.year - patient.date_of_birth.year - (
            (today.month, today.day) < (patient.date_of_birth.month, patient.date_of_birth.day)
        )
    
    # Generate alerts
    alerts = generate_vital_signs_alerts(latest_vitals, patient_age)
    
    return JsonResponse({
        'temperature': float(latest_vitals.temperature) if latest_vitals.temperature else None,
        'heart_rate': latest_vitals.heart_rate,
        'respiratory_rate': latest_vitals.respiratory_rate,
        'blood_pressure': latest_vitals.get_blood_pressure_display(),
        'oxygen_saturation': latest_vitals.oxygen_saturation,
        'height': float(latest_vitals.height) if latest_vitals.height else None,
        'weight': float(latest_vitals.weight) if latest_vitals.weight else None,
        'bmi': float(latest_vitals.bmi) if latest_vitals.bmi else None,
        'nutritional_status': latest_vitals.get_nutritional_status_display() if latest_vitals.nutritional_status else None,
        'last_updated': latest_vitals.medical_record.date.strftime('%Y-%m-%d %H:%M') if latest_vitals.medical_record.date else None,
        'alerts': alerts,
        'patient_age': patient_age,
    })

def generate_vital_signs_alerts(vital_signs, patient_age):
    """
    Generate alerts for abnormal vital signs values based on pediatric ranges
    """
    alerts = []
    
    if not patient_age:
        return alerts
    
    # Pediatric normal ranges (simplified - in production, use detailed age-specific ranges)
    normal_ranges = {
        'temperature': (36.1, 37.2),  # °C
        'heart_rate': (60, 120) if patient_age > 10 else (80, 140),  # bpm
        'respiratory_rate': (12, 20) if patient_age > 10 else (20, 30),  # /min
        'systolic_bp': (90, 120) if patient_age > 10 else (80, 110),  # mmHg
        'oxygen_saturation': (95, 100),  # %
    }
    
    # Check temperature
    if vital_signs.temperature:
        temp = float(vital_signs.temperature)
        if temp < normal_ranges['temperature'][0]:
            alerts.append({
                'type': 'warning',
                'category': 'temperature',
                'message': f'Température basse: {temp}°C',
                'severity': 'medium'
            })
        elif temp > normal_ranges['temperature'][1]:
            alerts.append({
                'type': 'danger',
                'category': 'temperature',
                'message': f'Fièvre: {temp}°C',
                'severity': 'high'
            })
    
    # Check heart rate
    if vital_signs.heart_rate:
        hr_min, hr_max = normal_ranges['heart_rate']
        if vital_signs.heart_rate < hr_min:
            alerts.append({
                'type': 'warning',
                'category': 'heart_rate',
                'message': f'Bradycardie: {vital_signs.heart_rate} bpm',
                'severity': 'medium'
            })
        elif vital_signs.heart_rate > hr_max:
            alerts.append({
                'type': 'danger',
                'category': 'heart_rate',
                'message': f'Tachycardie: {vital_signs.heart_rate} bpm',
                'severity': 'high'
            })
    
    # Check respiratory rate
    if vital_signs.respiratory_rate:
        rr_min, rr_max = normal_ranges['respiratory_rate']
        if vital_signs.respiratory_rate < rr_min:
            alerts.append({
                'type': 'warning',
                'category': 'respiratory_rate',
                'message': f'Bradypnée: {vital_signs.respiratory_rate}/min',
                'severity': 'medium'
            })
        elif vital_signs.respiratory_rate > rr_max:
            alerts.append({
                'type': 'danger',
                'category': 'respiratory_rate',
                'message': f'Tachypnée: {vital_signs.respiratory_rate}/min',
                'severity': 'high'
            })
    
    # Check oxygen saturation
    if vital_signs.oxygen_saturation:
        if vital_signs.oxygen_saturation < normal_ranges['oxygen_saturation'][0]:
            alerts.append({
                'type': 'danger',
                'category': 'oxygen_saturation',
                'message': f'Hypoxémie: {vital_signs.oxygen_saturation}%',
                'severity': 'high'
            })
    
    # Check nutritional status
    if vital_signs.nutritional_status in ['SEVERE_MALNUTRITION', 'MODERATE_MALNUTRITION']:
        alerts.append({
            'type': 'danger',
            'category': 'nutrition',
            'message': f'Malnutrition détectée: {vital_signs.get_nutritional_status_display()}',
            'severity': 'high'
        })
    elif vital_signs.nutritional_status == 'UNDERWEIGHT':
        alerts.append({
            'type': 'warning',
            'category': 'nutrition',
            'message': 'Insuffisance pondérale',
            'severity': 'medium'
        })
    elif vital_signs.nutritional_status == 'OBESITY':
        alerts.append({
            'type': 'warning',
            'category': 'nutrition',
            'message': 'Obésité détectée',
            'severity': 'medium'
        })
    
    return alerts

def calculate_growth_trends(vital_signs_records, patient_age):
    """
    Calculate growth trends and developmental progress
    """
    if not vital_signs_records.exists():
        return {}
    
    # Get first and latest records with growth data
    growth_records = vital_signs_records.filter(
        Q(height__isnull=False) | Q(weight__isnull=False)
    ).order_by('medical_record__date')
    
    if growth_records.count() < 2:
        return {'insufficient_data': True}
    
    first_record = growth_records.first()
    latest_record = growth_records.last()
    
    trends = {}
    
    # Height trend
    if first_record.height and latest_record.height:
        height_change = float(latest_record.height) - float(first_record.height)
        trends['height_change'] = height_change
        trends['height_trend'] = 'increasing' if height_change > 0 else 'stable'
    
    # Weight trend
    if first_record.weight and latest_record.weight:
        weight_change = float(latest_record.weight) - float(first_record.weight)
        trends['weight_change'] = weight_change
        trends['weight_trend'] = 'increasing' if weight_change > 0 else ('decreasing' if weight_change < 0 else 'stable')
    
    # BMI trend
    if first_record.bmi and latest_record.bmi:
        bmi_change = float(latest_record.bmi) - float(first_record.bmi)
        trends['bmi_change'] = bmi_change
        trends['bmi_trend'] = 'increasing' if bmi_change > 0.5 else ('decreasing' if bmi_change < -0.5 else 'stable')
    
    return trends

def prepare_vital_signs_chart_data(vital_signs_records):
    """
    Prepare data for Chart.js visualization
    """
    chart_data = {
        'labels': [],
        'datasets': {
            'temperature': [],
            'heart_rate': [],
            'weight': [],
            'height': [],
            'bmi': []
        }
    }
    
    # Get last 12 records for chart
    recent_records = vital_signs_records[:12]
    
    for vs in reversed(recent_records):
        date_label = vs.medical_record.date.strftime('%d/%m') if vs.medical_record.date else ''
        chart_data['labels'].append(date_label)
        
        chart_data['datasets']['temperature'].append(float(vs.temperature) if vs.temperature else None)
        chart_data['datasets']['heart_rate'].append(vs.heart_rate)
        chart_data['datasets']['weight'].append(float(vs.weight) if vs.weight else None)
        chart_data['datasets']['height'].append(float(vs.height) if vs.height else None)
        chart_data['datasets']['bmi'].append(float(vs.bmi) if vs.bmi else None)
    
    return chart_data

def generate_who_reference_data(gender, max_age_months):
    """
    Generate simplified WHO growth reference data for charts
    (In production, use actual WHO growth standards)
    """
    # Simplified WHO percentile data
    age_points = list(range(0, min(int(max_age_months) + 12, 216), 6))  # Every 6 months up to 18 years
    
    who_data = {
        'height': {
            'p3': [], 'p10': [], 'p25': [], 'p50': [], 'p75': [], 'p90': [], 'p97': []
        },
        'weight': {
            'p3': [], 'p10': [], 'p25': [], 'p50': [], 'p75': [], 'p90': [], 'p97': []
        }
    }
    
    for age in age_points:
        # Simplified height percentiles (cm) - these should be from actual WHO data
        if gender == 'M':  # Male
            height_50 = 50 + (age * 0.8)  # Simplified growth curve
            who_data['height']['p50'].append({'x': age, 'y': height_50})
            who_data['height']['p25'].append({'x': age, 'y': height_50 - 5})
            who_data['height']['p75'].append({'x': age, 'y': height_50 + 5})
            who_data['height']['p3'].append({'x': age, 'y': height_50 - 10})
            who_data['height']['p97'].append({'x': age, 'y': height_50 + 10})
        else:  # Female
            height_50 = 49 + (age * 0.75)  # Simplified growth curve
            who_data['height']['p50'].append({'x': age, 'y': height_50})
            who_data['height']['p25'].append({'x': age, 'y': height_50 - 4})
            who_data['height']['p75'].append({'x': age, 'y': height_50 + 4})
            who_data['height']['p3'].append({'x': age, 'y': height_50 - 8})
            who_data['height']['p97'].append({'x': age, 'y': height_50 + 8})
        
        # Simplified weight percentiles (kg)
        if gender == 'M':  # Male
            weight_50 = 3.3 + (age * 0.25)  # Simplified weight curve
            who_data['weight']['p50'].append({'x': age, 'y': weight_50})
            who_data['weight']['p25'].append({'x': age, 'y': weight_50 * 0.85})
            who_data['weight']['p75'].append({'x': age, 'y': weight_50 * 1.15})
            who_data['weight']['p3'].append({'x': age, 'y': weight_50 * 0.7})
            who_data['weight']['p97'].append({'x': age, 'y': weight_50 * 1.3})
        else:  # Female
            weight_50 = 3.2 + (age * 0.23)  # Simplified weight curve
            who_data['weight']['p50'].append({'x': age, 'y': weight_50})
            who_data['weight']['p25'].append({'x': age, 'y': weight_50 * 0.87})
            who_data['weight']['p75'].append({'x': age, 'y': weight_50 * 1.13})
            who_data['weight']['p3'].append({'x': age, 'y': weight_50 * 0.72})
            who_data['weight']['p97'].append({'x': age, 'y': weight_50 * 1.28})
    
    return who_data

@login_required
def hospitalization_list(request):
    """List all hospitalizations with filtering and search"""
    from .models import Hospitalization
    
    user_profile = request.user.profile
    
    # Base queryset based on user role
    if user_profile.user_type == 'superadmin':
        hospitalizations = Hospitalization.objects.all()
    elif user_profile.user_type == 'facility_admin':
        # Show hospitalizations for this facility
        facility = user_profile.facility
        hospitalizations = Hospitalization.objects.filter(
            patient__medicalrecord__facility=facility
        ).distinct()
    elif user_profile.user_type == 'doctor':
        # Show hospitalizations where this doctor is involved
        hospitalizations = Hospitalization.objects.filter(
            Q(admitting_doctor=user_profile) | Q(attending_doctor=user_profile)
        )
    else:
        hospitalizations = Hospitalization.objects.none()
    
    # Search and filters
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    room_filter = request.GET.get('room', '')
    doctor_filter = request.GET.get('doctor', '')
    date_filter = request.GET.get('date_filter', '')
    
    if search_query:
        hospitalizations = hospitalizations.filter(
            Q(patient__first_name__icontains=search_query) |
            Q(patient__last_name__icontains=search_query) |
            Q(patient__patient_id__icontains=search_query) |
            Q(admission_reason__icontains=search_query) |
            Q(admission_diagnosis__icontains=search_query)
        )
    
    if status_filter:
        hospitalizations = hospitalizations.filter(status=status_filter)
    
    if room_filter:
        hospitalizations = hospitalizations.filter(room_number=room_filter)
    
    if doctor_filter:
        hospitalizations = hospitalizations.filter(
            Q(admitting_doctor_id=doctor_filter) | Q(attending_doctor_id=doctor_filter)
        )
    
    # Date filtering
    if date_filter:
        today = timezone.now().date()
        if date_filter == 'today':
            hospitalizations = hospitalizations.filter(admission_date__date=today)
        elif date_filter == 'week':
            from datetime import timedelta
            week_start = today - timedelta(days=today.weekday())
            hospitalizations = hospitalizations.filter(admission_date__date__gte=week_start)
        elif date_filter == 'month':
            hospitalizations = hospitalizations.filter(
                admission_date__year=today.year,
                admission_date__month=today.month
            )
    
    hospitalizations = hospitalizations.select_related(
        'patient', 'admitting_doctor', 'attending_doctor'
    ).order_by('-admission_date')
    
    # Get filter options
    doctors = UserProfile.objects.filter(user_type='doctor')
    
    context = {
        'hospitalizations': hospitalizations,
        'total_count': hospitalizations.count(),
        'doctors': doctors,
        'status_choices': Hospitalization.STATUS_CHOICES,
        'room_choices': Hospitalization.ROOM_CHOICES,
        'filters': {
            'search_query': search_query,
            'status_filter': status_filter,
            'room_filter': room_filter,
            'doctor_filter': doctor_filter,
            'date_filter': date_filter,
        }
    }
    
    return render(request, 'patients/hospitalizations/list.html', context)


@login_required
def hospitalization_detail(request, pk):
    """View hospitalization details"""
    from .models import Hospitalization, HospitalizationProgressNote, DischargeReport
    
    hospitalization = get_object_or_404(Hospitalization, pk=pk)
    
    # Check permissions
    user_profile = request.user.profile
    if (user_profile.user_type == 'doctor' and 
        hospitalization.admitting_doctor != user_profile and 
        hospitalization.attending_doctor != user_profile):
        messages.error(request, "Vous n'avez pas accès à cette hospitalisation.")
        return redirect('patients:hospitalizations')
    
    # Get related data
    progress_notes = hospitalization.progress_notes.all().order_by('-date_time')
    discharge_report = getattr(hospitalization, 'discharge_report', None)
    
    context = {
        'hospitalization': hospitalization,
        'progress_notes': progress_notes,
        'discharge_report': discharge_report,
        'can_add_note': user_profile.user_type in ['doctor'],
        'can_discharge': (hospitalization.status == 'admitted' and 
                         user_profile.user_type in ['doctor'] and
                         hospitalization.attending_doctor == user_profile)
    }
    
    return render(request, 'patients/hospitalizations/detail.html', context)


@login_required
def hospitalization_create(request):
    """Create new hospitalization"""
    from .models import Hospitalization
    
    user_profile = request.user.profile
    
    if user_profile.user_type not in ['doctor', 'facility_admin']:
        messages.error(request, "Vous n'avez pas les permissions pour créer une hospitalisation.")
        return redirect('patients:hospitalizations')
    
    if request.method == 'POST':
        try:
            # Get form data
            patient_id = request.POST.get('patient')
            admission_reason = request.POST.get('admission_reason')
            admission_diagnosis = request.POST.get('admission_diagnosis')
            room_number = request.POST.get('room_number')
            bed_number = request.POST.get('bed_number')
            attending_doctor_id = request.POST.get('attending_doctor')
            
            # Validate required fields
            if not all([patient_id, admission_reason, admission_diagnosis, room_number, bed_number]):
                messages.error(request, "Veuillez remplir tous les champs obligatoires.")
                return render(request, 'patients/hospitalizations/create.html', {
                    'patients': Patient.objects.all(),
                    'doctors': UserProfile.objects.filter(user_type='doctor'),
                    'room_choices': Hospitalization.ROOM_CHOICES,
                    'form_data': request.POST
                })
            
            patient = get_object_or_404(Patient, id=patient_id)
            attending_doctor = get_object_or_404(UserProfile, id=attending_doctor_id) if attending_doctor_id else user_profile
            
            # Create hospitalization
            hospitalization = Hospitalization.objects.create(
                patient=patient,
                admission_date=timezone.now(),
                admitting_doctor=user_profile,
                attending_doctor=attending_doctor,
                admission_reason=admission_reason,
                admission_diagnosis=admission_diagnosis,
                room_number=room_number,
                bed_number=bed_number,
                status='admitted'
            )
            
            messages.success(request, f"Hospitalisation créée avec succès pour {patient.first_name} {patient.last_name}.")
            return redirect('patients:hospitalization_detail', pk=hospitalization.pk)
            
        except Exception as e:
            messages.error(request, f"Erreur lors de la création: {str(e)}")
    
    # GET request - show form
    context = {
        'patients': Patient.objects.all(),
        'doctors': UserProfile.objects.filter(user_type='doctor'),
        'room_choices': Hospitalization.ROOM_CHOICES,
    }
    
    return render(request, 'patients/hospitalizations/create.html', context)


@login_required
def add_progress_note(request, pk):
    """Add progress note to hospitalization"""
    from .models import Hospitalization, HospitalizationProgressNote
    
    hospitalization = get_object_or_404(Hospitalization, pk=pk)
    user_profile = request.user.profile
    
    # Check permissions
    if user_profile.user_type not in ['doctor']:
        messages.error(request, "Seuls les médecins peuvent ajouter des notes de progression.")
        return redirect('patients:hospitalization_detail', pk=pk)
    
    if request.method == 'POST':
        note_content = request.POST.get('note_content')
        vital_signs = request.POST.get('vital_signs', '')
        
        if note_content:
            HospitalizationProgressNote.objects.create(
                hospitalization=hospitalization,
                doctor=user_profile,
                note_content=note_content,
                vital_signs=vital_signs
            )
            messages.success(request, "Note de progression ajoutée avec succès.")
        else:
            messages.error(request, "Le contenu de la note est requis.")
    
    return redirect('patients:hospitalization_detail', pk=pk)
