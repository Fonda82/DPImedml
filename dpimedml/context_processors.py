from patients.models import Patient

def current_patient(request):
    """
    Context processor to make current patient available in all templates
    """
    context = {}
    
    if request.user.is_authenticated and hasattr(request.user, 'profile'):
        if request.user.profile.user_type == 'patient':
            try:
                current_patient = Patient.objects.get(user=request.user)
                context['current_patient'] = current_patient
            except Patient.DoesNotExist:
                context['current_patient'] = None
    
    return context 