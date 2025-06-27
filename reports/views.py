from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def system_report(request):
    """Display system-level reports and analytics"""
    # For demo purposes, just a placeholder
    context = {
        'title': 'Rapport système',
        'subtitle': 'Statistiques globales et analyses de performance',
    }
    return render(request, 'reports/system.html', context) 