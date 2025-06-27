from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from django.utils import timezone
from .models import Facility, InterFacilityCommunication
from accounts.models import UserProfile

# Create your views here.

@login_required
def facility_list(request):
    # Get all facilities from database
    facilities = Facility.objects.all().order_by('name')
    return render(request, 'facilities/list.html', {'facilities': facilities})

@login_required
def facility_detail(request, pk):
    # Get actual facility data from database
    facility = get_object_or_404(Facility, pk=pk)
    
    # Get staff associated with this facility
    staff = UserProfile.objects.filter(facility=facility)
    
    return render(request, 'facilities/detail.html', {'facility': facility, 'staff': staff})

@login_required
def facility_create(request):
    """View for creating a new facility"""
    # Check if user has permission to create facilities
    if request.user.profile.user_type not in ['superadmin', 'facility_admin']:
        messages.error(request, "Vous n'avez pas la permission de créer un établissement.")
        return redirect('dashboard:index')
    
    if request.method == 'POST':
        # Extract form data
        name = request.POST.get('name', '')
        facility_type = request.POST.get('facility_type', '')
        address = request.POST.get('address', '')
        city = request.POST.get('city', 'Bamako')
        region = request.POST.get('region', '')
        country = request.POST.get('country', 'Mali')
        phone = request.POST.get('phone', '')
        email = request.POST.get('email', '')
        year_established = request.POST.get('year_established', None)
        is_active = request.POST.get('is_active') == 'on'
        
        # Validate required fields
        if not all([name, facility_type, address, city]):
            messages.error(request, "Veuillez remplir tous les champs obligatoires.")
            return render(request, 'facilities/create.html')
        
        # Create a new facility
        new_facility = Facility(
            name=name,
            facility_type=facility_type,
            address=address,
            city=city,
            region=region,
            country=country,
            phone=phone,
            email=email,
            is_active=is_active
        )
        
        # Handle optional year_established
        if year_established:
            try:
                new_facility.year_established = int(year_established)
            except (ValueError, TypeError):
                pass
                
        new_facility.save()
        
        # Add system activity
        try:
            from dashboard.models import SystemActivity
            SystemActivity.objects.create(
                user=request.user,
                action='Nouvel établissement créé',
                description=f'Établissement {name} créé par {request.user.username}',
                action_type='create'
            )
        except ImportError:
            pass
        
        messages.success(request, f"L'établissement {name} a été créé avec succès.")
        return redirect('facilities:detail', pk=new_facility.pk)
        
    return render(request, 'facilities/create.html')

@login_required
def facility_edit(request, pk):
    """View for editing an existing facility"""
    # Get actual facility data from database
    facility = get_object_or_404(Facility, pk=pk)
    
    # Check if user has permission to edit facilities
    if request.user.profile.user_type not in ['superadmin', 'facility_admin']:
        messages.error(request, "Vous n'avez pas la permission de modifier un établissement.")
        return redirect('dashboard:index')
        
    # If facility admin, check if they belong to this facility
    if request.user.profile.user_type == 'facility_admin' and request.user.profile.facility != facility:
        messages.error(request, "Vous n'avez pas la permission de modifier cet établissement.")
        return redirect('dashboard:index')
    
    if request.method == 'POST':
        # Update facility with form data
        facility.name = request.POST.get('name', facility.name)
        facility.facility_type = request.POST.get('facility_type', facility.facility_type)
        facility.address = request.POST.get('address', facility.address)
        facility.phone = request.POST.get('phone', facility.phone)
        facility.email = request.POST.get('email', facility.email)
        facility.save()
        
        messages.success(request, "L'établissement a été modifié avec succès.")
        return redirect('facilities:detail', pk=pk)
        
    return render(request, 'facilities/edit.html', {'facility': facility})

@login_required
def communication_list(request):
    """List all inter-facility communications with filtering and search"""
    user_profile = request.user.profile
    
    # Base queryset based on user role
    if user_profile.user_type == 'superadmin':
        communications = InterFacilityCommunication.objects.all()
    elif user_profile.user_type == 'facility_admin':
        # Show communications for this facility (both sent and received)
        facility = user_profile.facility
        communications = InterFacilityCommunication.objects.filter(
            Q(from_facility=facility) | Q(to_facility=facility)
        )
    elif user_profile.user_type == 'doctor':
        # Show communications sent or received by this doctor
        communications = InterFacilityCommunication.objects.filter(
            Q(sent_by=user_profile) | Q(received_by=user_profile)
        )
    else:
        communications = InterFacilityCommunication.objects.none()
    
    # Search and filters
    search_query = request.GET.get('search', '')
    type_filter = request.GET.get('type', '')
    status_filter = request.GET.get('status', '')
    facility_filter = request.GET.get('facility', '')
    urgent_filter = request.GET.get('urgent', '')
    date_filter = request.GET.get('date_filter', '')
    
    if search_query:
        communications = communications.filter(
            Q(subject__icontains=search_query) |
            Q(message__icontains=search_query) |
            Q(communication_id__icontains=search_query) |
            Q(from_facility__name__icontains=search_query) |
            Q(to_facility__name__icontains=search_query)
        )
    
    if type_filter:
        communications = communications.filter(communication_type=type_filter)
    
    if status_filter:
        communications = communications.filter(status=status_filter)
    
    if facility_filter:
        communications = communications.filter(
            Q(from_facility_id=facility_filter) | Q(to_facility_id=facility_filter)
        )
    
    if urgent_filter == 'yes':
        communications = communications.filter(is_urgent=True)
    
    # Date filtering
    if date_filter:
        today = timezone.now().date()
        if date_filter == 'today':
            communications = communications.filter(sent_date__date=today)
        elif date_filter == 'week':
            from datetime import timedelta
            week_start = today - timedelta(days=today.weekday())
            communications = communications.filter(sent_date__date__gte=week_start)
        elif date_filter == 'month':
            communications = communications.filter(
                sent_date__year=today.year,
                sent_date__month=today.month
            )
    
    communications = communications.select_related(
        'from_facility', 'to_facility', 'sent_by', 'received_by'
    ).order_by('-sent_date')
    
    # Get filter options
    facilities = Facility.objects.all()
    
    context = {
        'communications': communications,
        'total_count': communications.count(),
        'facilities': facilities,
        'type_choices': InterFacilityCommunication.COMMUNICATION_TYPES,
        'status_choices': InterFacilityCommunication.STATUS_CHOICES,
        'filters': {
            'search_query': search_query,
            'type_filter': type_filter,
            'status_filter': status_filter,
            'facility_filter': facility_filter,
            'urgent_filter': urgent_filter,
            'date_filter': date_filter,
        }
    }
    
    return render(request, 'facilities/communications/list.html', context)


@login_required
def communication_detail(request, pk):
    """View communication details"""
    communication = get_object_or_404(InterFacilityCommunication, pk=pk)
    
    # Check permissions
    user_profile = request.user.profile
    if (user_profile.user_type == 'doctor' and 
        communication.sent_by != user_profile and 
        communication.received_by != user_profile):
        messages.error(request, "Vous n'avez pas accès à cette communication.")
        return redirect('facilities:communications')
    elif (user_profile.user_type == 'facility_admin' and 
          communication.from_facility != user_profile.facility and 
          communication.to_facility != user_profile.facility):
        messages.error(request, "Vous n'avez pas accès à cette communication.")
        return redirect('facilities:communications')
    
    # Mark as read if user is the recipient
    if (communication.to_facility == user_profile.facility and 
        communication.status == 'delivered' and 
        not communication.read_date):
        communication.status = 'read'
        communication.read_date = timezone.now()
        communication.received_by = user_profile
        communication.save()
    
    context = {
        'communication': communication,
        'can_respond': (user_profile.user_type in ['doctor', 'facility_admin'] and 
                       communication.to_facility == user_profile.facility and 
                       communication.requires_response and 
                       not communication.response_date)
    }
    
    return render(request, 'facilities/communications/detail.html', context)


@login_required
def communication_create(request):
    """Create new inter-facility communication"""
    user_profile = request.user.profile
    
    if user_profile.user_type not in ['doctor', 'facility_admin']:
        messages.error(request, "Vous n'avez pas les permissions pour envoyer une communication.")
        return redirect('facilities:communications')
    
    if request.method == 'POST':
        try:
            # Get form data
            to_facility_id = request.POST.get('to_facility')
            communication_type = request.POST.get('communication_type')
            subject = request.POST.get('subject')
            message = request.POST.get('message')
            is_urgent = request.POST.get('is_urgent') == 'on'
            requires_response = request.POST.get('requires_response') == 'on'
            
            # Validate required fields
            if not all([to_facility_id, communication_type, subject, message]):
                messages.error(request, "Veuillez remplir tous les champs obligatoires.")
                return render(request, 'facilities/communications/create.html', {
                    'facilities': Facility.objects.exclude(id=user_profile.facility.id if user_profile.facility else None),
                    'type_choices': InterFacilityCommunication.COMMUNICATION_TYPES,
                    'form_data': request.POST
                })
            
            to_facility = get_object_or_404(Facility, id=to_facility_id)
            
            # Create communication
            communication = InterFacilityCommunication.objects.create(
                from_facility=user_profile.facility,
                to_facility=to_facility,
                communication_type=communication_type,
                subject=subject,
                message=message,
                sent_by=user_profile,
                is_urgent=is_urgent,
                requires_response=requires_response,
                status='sent'
            )
            
            # Mark as delivered immediately (simulating instant delivery)
            communication.status = 'delivered'
            communication.delivered_date = timezone.now()
            communication.save()
            
            messages.success(request, f"Message envoyé avec succès à {to_facility.name}.")
            return redirect('facilities:communication_detail', pk=communication.pk)
            
        except Exception as e:
            messages.error(request, f"Erreur lors de l'envoi: {str(e)}")
    
    # GET request - show form
    context = {
        'facilities': Facility.objects.exclude(id=user_profile.facility.id if user_profile.facility else None),
        'type_choices': InterFacilityCommunication.COMMUNICATION_TYPES,
    }
    
    return render(request, 'facilities/communications/create.html', context)


@login_required
def communication_respond(request, pk):
    """Respond to a communication"""
    communication = get_object_or_404(InterFacilityCommunication, pk=pk)
    user_profile = request.user.profile
    
    # Check permissions
    if (communication.to_facility != user_profile.facility or 
        user_profile.user_type not in ['doctor', 'facility_admin']):
        messages.error(request, "Vous n'avez pas les permissions pour répondre à cette communication.")
        return redirect('facilities:communication_detail', pk=pk)
    
    if not communication.requires_response:
        messages.warning(request, "Cette communication ne nécessite pas de réponse.")
        return redirect('facilities:communication_detail', pk=pk)
    
    if communication.response_date:
        messages.warning(request, "Cette communication a déjà reçu une réponse.")
        return redirect('facilities:communication_detail', pk=pk)
    
    if request.method == 'POST':
        response_message = request.POST.get('response_message')
        
        if response_message:
            communication.response_message = response_message
            communication.response_by = user_profile
            communication.response_date = timezone.now()
            communication.status = 'responded'
            communication.save()
            
            messages.success(request, "Réponse envoyée avec succès.")
        else:
            messages.error(request, "Le message de réponse est requis.")
    
    return redirect('facilities:communication_detail', pk=pk)
