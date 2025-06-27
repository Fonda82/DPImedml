from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Count, Sum
from django.utils import timezone
from datetime import timedelta, date
from django.template.loader import render_to_string
from django.core.paginator import Paginator

from .models import (
    Prescription, Medication, PrescriptionMedication, 
    MedicationCategory, PrescriptionTemplate, TemplateMedication
)
from patients.models import Patient, MedicalRecord, VitalSigns
from accounts.models import UserProfile
from facilities.models import Facility

@login_required
def prescription_list(request):
    """
    Display list of prescriptions with smart filtering for Mali healthcare context
    """
    user_type = request.user.profile.user_type
    
    # Base queryset with role-based filtering
    if user_type == 'patient':
        # Patients see only their own prescriptions
        try:
            patient = Patient.objects.get(user=request.user)
            prescriptions = Prescription.objects.filter(patient=patient)
        except Patient.DoesNotExist:
            prescriptions = Prescription.objects.none()
    elif user_type == 'doctor':
        # Doctors see prescriptions they've created
        if request.user.username == 'docteur':  # Demo doctor sees all
            prescriptions = Prescription.objects.all()
        else:
            prescriptions = Prescription.objects.filter(prescribing_doctor=request.user.profile)
    elif user_type == 'facility_admin':
        # Facility admins see prescriptions from their facility
        prescriptions = Prescription.objects.filter(prescribing_facility=request.user.profile.facility)
    else:
        # Superadmins see all
        prescriptions = Prescription.objects.all()
    
    # Apply filters
    status_filter = request.GET.get('status', '')
    priority_filter = request.GET.get('priority', '')
    date_filter = request.GET.get('date_filter', '')
    search_query = request.GET.get('search', '').strip()
    
    if status_filter:
        prescriptions = prescriptions.filter(status=status_filter)
    
    if priority_filter:
        prescriptions = prescriptions.filter(priority=priority_filter)
    
    if search_query:
        search_filter = Q(prescription_id__icontains=search_query) | \
                       Q(patient__first_name__icontains=search_query) | \
                       Q(patient__last_name__icontains=search_query) | \
                       Q(patient__patient_id__icontains=search_query) | \
                       Q(diagnosis__icontains=search_query)
        prescriptions = prescriptions.filter(search_filter)
    
    # Date filtering
    if date_filter == 'today':
        today = date.today()
        prescriptions = prescriptions.filter(prescribed_date__date=today)
    elif date_filter == 'week':
        start_week = date.today() - timedelta(days=date.today().weekday())
        end_week = start_week + timedelta(days=6)
        prescriptions = prescriptions.filter(prescribed_date__date__range=[start_week, end_week])
    elif date_filter == 'month':
        today = date.today()
        start_month = today.replace(day=1)
        prescriptions = prescriptions.filter(prescribed_date__date__gte=start_month)
    
    # Order by most recent
    prescriptions = prescriptions.select_related(
        'patient', 'prescribing_doctor__user', 'prescribing_facility'
    ).order_by('-prescribed_date')
    
    # Pagination
    paginator = Paginator(prescriptions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistics for dashboard
    stats = {
        'total': prescriptions.count(),
        'draft': prescriptions.filter(status='DRAFT').count(),
        'prescribed': prescriptions.filter(status='PRESCRIBED').count(),
        'dispensed': prescriptions.filter(status='DISPENSED').count(),
        'expired': prescriptions.filter(status='EXPIRED').count(),
    }
    
    context = {
        'page_obj': page_obj,
        'prescriptions': page_obj,
        'stats': stats,
        'status_choices': Prescription.STATUS_CHOICES,
        'priority_choices': Prescription.PRIORITY_CHOICES,
        'filters': {
            'status': status_filter,
            'priority': priority_filter,
            'date_filter': date_filter,
            'search': search_query,
        }
    }
    
    return render(request, 'prescriptions/list.html', context)

@login_required
def prescription_detail(request, pk):
    """
    Display detailed view of a prescription with medications and workflow status
    """
    prescription = get_object_or_404(Prescription, pk=pk)
    
    # Check permissions
    user_type = request.user.profile.user_type
    if user_type == 'patient' and prescription.patient.user != request.user:
        messages.error(request, "Vous n'avez pas la permission de voir cette prescription.")
        return redirect('prescriptions:list')
    
    # Get prescription medications
    prescription_medications = PrescriptionMedication.objects.filter(
        prescription=prescription
    ).select_related('medication', 'medication__category')
    
    context = {
        'prescription': prescription,
        'prescription_medications': prescription_medications,
        'can_edit': user_type in ['doctor', 'superadmin'] and prescription.status == 'DRAFT',
        'can_validate': user_type in ['pharmacist', 'superadmin'] and prescription.status == 'PRESCRIBED',
        'can_dispense': user_type in ['pharmacist', 'superadmin'] and prescription.status == 'VALIDATED',
    }
    
    return render(request, 'prescriptions/detail.html', context)

@login_required
def prescription_create(request):
    """
    Create a new prescription - redirect to patient selection
    """
    # Search for patients
    search_query = request.GET.get('search', '').strip()
    
    patients = Patient.objects.all()
    if search_query:
        search_filter = Q(first_name__icontains=search_query) | \
                       Q(last_name__icontains=search_query) | \
                       Q(patient_id__icontains=search_query)
        patients = patients.filter(search_filter)
    
    patients = patients.order_by('last_name', 'first_name')[:20]  # Limit for performance
    
    context = {
        'patients': patients,
        'search_query': search_query
    }
    
    return render(request, 'prescriptions/select_patient.html', context)

@login_required
def prescription_create_for_patient(request, patient_id):
    """
    Create a new prescription for a specific patient
    """
    patient = get_object_or_404(Patient, pk=patient_id)
    
    # Check permissions
    if request.user.profile.user_type not in ['doctor', 'superadmin']:
        messages.error(request, "Vous n'avez pas la permission de créer des prescriptions.")
        return redirect('prescriptions:list')
    
    if request.method == 'POST':
        # Create prescription
        prescription = Prescription(
            patient=patient,
            prescribing_doctor=request.user.profile,
            prescribing_facility=getattr(request.user.profile, 'facility', None),
            diagnosis=request.POST.get('diagnosis', ''),
            clinical_notes=request.POST.get('clinical_notes', ''),
            instructions=request.POST.get('instructions', ''),
            priority=request.POST.get('priority', 'NORMAL'),
            status='DRAFT'
        )
        
        # Link to medical record if provided
        medical_record_id = request.POST.get('medical_record')
        if medical_record_id:
            try:
                medical_record = MedicalRecord.objects.get(id=medical_record_id, patient=patient)
                prescription.medical_record = medical_record
            except MedicalRecord.DoesNotExist:
                pass
        
        prescription.save()
        
        # Process medications
        medication_ids = request.POST.getlist('medication_id')
        doses = request.POST.getlist('dose')
        dose_units = request.POST.getlist('dose_unit')
        frequencies = request.POST.getlist('frequency')
        durations = request.POST.getlist('duration')
        routes = request.POST.getlist('route')
        instructions = request.POST.getlist('medication_instructions')
        
        for i, med_id in enumerate(medication_ids):
            if med_id and i < len(doses) and doses[i]:
                try:
                    medication = Medication.objects.get(id=med_id)
                    
                    # Calculate total quantity needed
                    dose = float(doses[i])
                    duration = int(durations[i]) if i < len(durations) and durations[i] else 7
                    freq_num = int(''.join(filter(str.isdigit, frequencies[i]))) if i < len(frequencies) else 1
                    total_quantity = dose * freq_num * duration
                    
                    PrescriptionMedication.objects.create(
                        prescription=prescription,
                        medication=medication,
                        dose=dose,
                        dose_unit=dose_units[i] if i < len(dose_units) else medication.unit,
                        frequency=frequencies[i] if i < len(frequencies) else '1 fois par jour',
                        route=routes[i] if i < len(routes) else 'ORAL',
                        duration_days=duration,
                        total_quantity=total_quantity,
                        instructions=instructions[i] if i < len(instructions) else '',
                    )
                except (Medication.DoesNotExist, ValueError):
                    continue
        
        messages.success(request, f"Prescription {prescription.prescription_id} créée avec succès.")
        return redirect('prescriptions:detail', pk=prescription.pk)
    
    # GET request - show form
    # Get patient's medical records for context
    medical_records = MedicalRecord.objects.filter(patient=patient).order_by('-date')[:5]
    
    # Get latest vital signs for dosing calculations
    latest_vitals = None
    if medical_records.exists():
        latest_vitals = VitalSigns.objects.filter(
            medical_record__patient=patient
        ).order_by('-medical_record__date').first()
    
    # Get available medications
    medications = Medication.objects.filter(
        is_pediatric_approved=True,
        available_in_mali=True
    ).select_related('category').order_by('name')
    
    # Get prescription templates
    templates = PrescriptionTemplate.objects.filter(
        is_mali_standard=True
    ).order_by('name')
    
    context = {
        'patient': patient,
        'medical_records': medical_records,
        'latest_vitals': latest_vitals,
        'medications': medications,
        'templates': templates,
        'status_choices': Prescription.STATUS_CHOICES,
        'priority_choices': Prescription.PRIORITY_CHOICES,
        'route_choices': PrescriptionMedication.ROUTE_CHOICES,
    }
    
    return render(request, 'prescriptions/create.html', context)

@login_required
def medication_search(request):
    """
    AJAX endpoint for searching medications with pediatric dosing
    """
    query = request.GET.get('q', '').strip()
    patient_id = request.GET.get('patient_id')
    
    if len(query) < 2:
        return JsonResponse({'medications': []})
    
    # Get patient for weight-based dosing
    patient = None
    patient_weight = None
    patient_age_months = None
    
    if patient_id:
        try:
            patient = Patient.objects.get(id=patient_id)
            # Get latest weight from vital signs
            latest_vitals = VitalSigns.objects.filter(
                medical_record__patient=patient
            ).order_by('-medical_record__date').first()
            
            if latest_vitals and latest_vitals.weight:
                patient_weight = float(latest_vitals.weight)
            
            # Calculate patient age in months
            if patient.date_of_birth:
                today = date.today()
                age_years = today.year - patient.date_of_birth.year
                age_months = (today.month - patient.date_of_birth.month)
                patient_age_months = (age_years * 12) + age_months
        except Patient.DoesNotExist:
            pass
    
    # Search medications
    search_filter = Q(name__icontains=query) | Q(generic_name__icontains=query)
    medications = Medication.objects.filter(
        search_filter,
        is_pediatric_approved=True,
        available_in_mali=True
    ).select_related('category')[:20]
    
    medications_data = []
    for med in medications:
        med_data = {
            'id': med.id,
            'name': med.name,
            'generic_name': med.generic_name,
            'form': med.get_form_display(),
            'strength': med.strength,
            'unit': med.unit,
            'category': med.category.name if med.category else '',
            'pediatric_approved': med.is_pediatric_approved,
        }
        
        # Calculate pediatric dose if patient info available
        if patient_weight and patient_age_months:
            dose_info = med.get_pediatric_dose(patient_weight, patient_age_months)
            if dose_info:
                med_data['suggested_dose'] = dose_info['dose']
                med_data['suggested_frequency'] = dose_info['frequency']
                med_data['dose_unit'] = dose_info['unit']
        
        medications_data.append(med_data)
    
    return JsonResponse({'medications': medications_data})

@login_required
def prescription_validate(request, pk):
    """
    Validate a prescription (pharmacist workflow)
    """
    prescription = get_object_or_404(Prescription, pk=pk)
    
    if request.user.profile.user_type not in ['pharmacist', 'superadmin']:
        messages.error(request, "Vous n'avez pas la permission de valider cette prescription.")
        return redirect('prescriptions:detail', pk=pk)
    
    if prescription.status != 'PRESCRIBED':
        messages.error(request, "Cette prescription ne peut pas être validée dans son état actuel.")
        return redirect('prescriptions:detail', pk=pk)
    
    prescription.status = 'VALIDATED'
    prescription.validated_date = timezone.now()
    prescription.validating_pharmacist = request.user.profile
    prescription.save()
    
    messages.success(request, f"Prescription {prescription.prescription_id} validée avec succès.")
    return redirect('prescriptions:detail', pk=pk)

@login_required
def prescription_dispense(request, pk):
    """
    Mark prescription as dispensed
    """
    prescription = get_object_or_404(Prescription, pk=pk)
    
    if request.user.profile.user_type not in ['pharmacist', 'superadmin']:
        messages.error(request, "Vous n'avez pas la permission de délivrer cette prescription.")
        return redirect('prescriptions:detail', pk=pk)
    
    if prescription.status != 'VALIDATED':
        messages.error(request, "Cette prescription doit être validée avant d'être délivrée.")
        return redirect('prescriptions:detail', pk=pk)
    
    prescription.status = 'DISPENSED'
    prescription.dispensed_date = timezone.now()
    prescription.dispensing_pharmacist = request.user.profile
    prescription.dispensing_facility = getattr(request.user.profile, 'facility', None)
    prescription.save()
    
    # Mark all medications as dispensed
    PrescriptionMedication.objects.filter(prescription=prescription).update(
        is_dispensed=True,
        dispensed_date=timezone.now(),
        dispensed_quantity=models.F('total_quantity')
    )
    
    messages.success(request, f"Prescription {prescription.prescription_id} délivrée avec succès.")
    return redirect('prescriptions:detail', pk=pk)

@login_required
def prescription_cancel(request, pk):
    """
    Cancel a prescription
    """
    prescription = get_object_or_404(Prescription, pk=pk)
    
    if request.user.profile.user_type not in ['doctor', 'superadmin']:
        messages.error(request, "Vous n'avez pas la permission d'annuler cette prescription.")
        return redirect('prescriptions:detail', pk=pk)
    
    if prescription.status in ['DISPENSED', 'COMPLETED']:
        messages.error(request, "Cette prescription ne peut plus être annulée.")
        return redirect('prescriptions:detail', pk=pk)
    
    prescription.status = 'CANCELLED'
    prescription.save()
    
    messages.success(request, f"Prescription {prescription.prescription_id} annulée.")
    return redirect('prescriptions:detail', pk=pk)

# Placeholder views (to be implemented)
@login_required
def prescription_edit(request, pk):
    messages.info(request, "Modification de prescription - En développement")
    return redirect('prescriptions:detail', pk=pk)

@login_required
def prescription_print(request, pk):
    messages.info(request, "Impression de prescription - En développement")
    return redirect('prescriptions:detail', pk=pk)

@login_required
def medication_list(request):
    messages.info(request, "Liste des médicaments - En développement")
    return redirect('prescriptions:list')

@login_required
def medication_detail(request, pk):
    messages.info(request, "Détail médicament - En développement")
    return redirect('prescriptions:list')

@login_required
def template_list(request):
    messages.info(request, "Protocoles de prescription - En développement")
    return redirect('prescriptions:list')

@login_required
def template_detail(request, pk):
    messages.info(request, "Détail protocole - En développement")
    return redirect('prescriptions:list')

@login_required
def apply_template(request, pk, patient_id):
    messages.info(request, "Application de protocole - En développement")
    return redirect('prescriptions:create_for_patient', patient_id=patient_id)

@login_required
def prescription_dashboard(request):
    messages.info(request, "Tableau de bord prescriptions - En développement")
    return redirect('prescriptions:list')

@login_required
def prescription_reports(request):
    messages.info(request, "Rapports prescriptions - En développement")
    return redirect('prescriptions:list')

@login_required
def calculate_medication_dose(request):
    """
    API endpoint for calculating pediatric medication doses
    """
    medication_id = request.GET.get('medication_id')
    weight = request.GET.get('weight')
    age_months = request.GET.get('age_months')
    
    try:
        medication = Medication.objects.get(id=medication_id)
        weight_kg = float(weight) if weight else None
        age = int(age_months) if age_months else None
        
        dose_info = medication.get_pediatric_dose(weight_kg, age)
        
        if dose_info:
            return JsonResponse({
                'success': True,
                'dose': dose_info['dose'],
                'frequency': dose_info['frequency'],
                'unit': dose_info['unit'],
                'form': dose_info['form']
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Impossible de calculer la dose pour ce patient'
            })
    
    except (Medication.DoesNotExist, ValueError):
        return JsonResponse({
            'success': False,
            'error': 'Médicament ou paramètres invalides'
        })

@login_required
def check_drug_interactions(request):
    """
    API endpoint for checking drug interactions (simplified)
    """
    medication_ids = request.GET.getlist('medications[]')
    
    # Simplified interaction check - in production, use a real drug interaction database
    interactions = []
    
    if len(medication_ids) > 1:
        medications = Medication.objects.filter(id__in=medication_ids)
        # Simple example interactions
        for med in medications:
            if 'paracetamol' in med.name.lower() and any('aspirine' in m.name.lower() for m in medications):
                interactions.append({
                    'severity': 'moderate',
                    'message': 'Attention: Interaction possible entre paracétamol et aspirine'
                })
    
    return JsonResponse({
        'interactions': interactions,
        'count': len(interactions)
    })
