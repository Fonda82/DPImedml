from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages
from .models import UserProfile

def login_demo(request):
    """
    Demo login view that allows selecting a user role without actual authentication.
    For demonstration purposes only.
    """
    if request.method == 'POST':
        # Check if we're using the automatic demo login (username from form)
        # or the username/password authentication
        user_type = request.POST.get('user_type')
        username = request.POST.get('username')
        
        # If username is provided without user_type, extract user_type from it
        # For demo_doctor format usernames
        if username and not user_type:
            if username.startswith('superadmin'):
                user_type = 'superadmin'
            elif username.startswith('facilityAdmin'):
                user_type = 'facility_admin'
            elif username.startswith('docteur'):
                user_type = 'doctor'
            elif username.startswith('patient'):
                user_type = 'patient'
        
        # For demo purposes, we'll create or get a user based on the selected role
        if user_type:
            # Use consistent demo usernames
            if user_type == 'superadmin':
                username = 'superadmin'
            elif user_type == 'facility_admin':
                username = 'facilityAdmin'
            elif user_type == 'doctor':
                username = 'docteur'
            elif user_type == 'patient':
                username = 'patient'
            
            # Create or get user
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f"{username}@example.com",
                    'first_name': user_type.replace('_', ' ').title(),
                    'last_name': 'Demo'
                }
            )
            
            # Set password for demo users
            if created:
                user.set_password('demo1234')
                user.save()
            
            # Set or update the user type in the user's profile
            if hasattr(user, 'profile'):
                user.profile.user_type = user_type
                user.profile.save()
            
            # Log the user in
            login(request, user)
            messages.success(request, f"Connecté en tant que {user_type}")
            return redirect('dashboard:index')
            
        else:
            # Authentication failed
            messages.error(request, "Sélection de rôle invalide.")
    
    # Add current_year to context for copyright
    import datetime
    context = {
        'current_year': datetime.datetime.now().year,
    }
    return render(request, 'accounts/login.html', context)

@login_required
def logout_demo(request):
    """Logout the current user"""
    logout(request)
    messages.info(request, "Vous avez été déconnecté.")
    return redirect('accounts:login')

@login_required
def profile(request):
    """Display and edit user profile"""
    return render(request, 'accounts/profile.html')

@login_required
def switch_role(request, role):
    """Switch between different roles for demo purposes"""
    if role in [choice[0] for choice in UserProfile.USER_TYPES]:
        # Log out current user
        logout(request)
        
        # Get or create a user with the selected role
        username = f"demo_{role}"
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': f"{username}@example.com",
                'first_name': role.replace('_', ' ').title(),
                'last_name': 'Demo'
            }
        )
        
        # Set or update the user type in the user's profile
        if hasattr(user, 'profile'):
            user.profile.user_type = role
            user.profile.save()
        
        # Log in as the new role
        login(request, user)
        messages.success(request, f"Rôle changé: {role}")
    
    return redirect('dashboard:index')

@login_required
def user_create(request):
    """Create a new user"""
    # For demo purposes, just render a template
    return render(request, 'accounts/user_create.html')

@login_required
def staff_list(request):
    """Display a list of all staff members"""
    # For demo purposes, create dummy staff data
    staff = [
        {'id': 1, 'first_name': 'Adama', 'last_name': 'Traoré', 'email': 'a.traore@example.com', 'specialty': 'Pédiatrie', 'role': 'doctor'},
        {'id': 2, 'first_name': 'Fatoumata', 'last_name': 'Ballo', 'email': 'f.ballo@example.com', 'specialty': 'Physiothérapie', 'role': 'doctor'},
        {'id': 3, 'first_name': 'Ibrahim', 'last_name': 'Dembélé', 'email': 'i.dembele@example.com', 'specialty': 'Orthophonie', 'role': 'doctor'},
        {'id': 4, 'first_name': 'Mariam', 'last_name': 'Keita', 'email': 'm.keita@example.com', 'specialty': 'Administration', 'role': 'admin'},
        {'id': 5, 'first_name': 'Oumar', 'last_name': 'Diallo', 'email': 'o.diallo@example.com', 'specialty': 'Support', 'role': 'staff'},
    ]
    
    return render(request, 'accounts/staff_list.html', {'staff': staff})

@login_required
def staff_detail(request, pk):
    """Display details about a staff member"""
    # For demo purposes, create dummy staff data based on ID
    staff_members = {
        1: {'id': 1, 'first_name': 'Adama', 'last_name': 'Traoré', 'email': 'a.traore@example.com', 'specialty': 'Pédiatrie', 'role': 'doctor', 'phone': '+223 70 12 34 56', 'address': 'Bamako, Mali', 'joined_date': '2020-01-15'},
        2: {'id': 2, 'first_name': 'Fatoumata', 'last_name': 'Ballo', 'email': 'f.ballo@example.com', 'specialty': 'Physiothérapie', 'role': 'doctor', 'phone': '+223 76 78 90 12', 'address': 'Bamako, Mali', 'joined_date': '2021-03-22'},
        3: {'id': 3, 'first_name': 'Ibrahim', 'last_name': 'Dembélé', 'email': 'i.dembele@example.com', 'specialty': 'Orthophonie', 'role': 'doctor', 'phone': '+223 79 67 45 23', 'address': 'Bamako, Mali', 'joined_date': '2019-11-05'},
    }
    
    staff_member = staff_members.get(pk, {'id': pk, 'first_name': 'Staff', 'last_name': 'Member', 'email': 'staff@example.com', 'specialty': 'Unknown', 'role': 'unknown', 'phone': 'Unknown', 'address': 'Unknown', 'joined_date': 'Unknown'})
    
    return render(request, 'accounts/staff_detail.html', {'staff': staff_member})

@login_required
def staff_edit(request, pk):
    """Edit a staff member"""
    # For demo purposes, create dummy staff data based on ID
    staff_members = {
        1: {'id': 1, 'first_name': 'Adama', 'last_name': 'Traoré', 'email': 'a.traore@example.com', 'specialty': 'Pédiatrie', 'role': 'doctor'},
        2: {'id': 2, 'first_name': 'Fatoumata', 'last_name': 'Ballo', 'email': 'f.ballo@example.com', 'specialty': 'Physiothérapie', 'role': 'doctor'},
        3: {'id': 3, 'first_name': 'Ibrahim', 'last_name': 'Dembélé', 'email': 'i.dembele@example.com', 'specialty': 'Orthophonie', 'role': 'doctor'},
    }
    
    staff_member = staff_members.get(pk, {'id': pk, 'first_name': 'Staff', 'last_name': 'Member', 'email': 'staff@example.com', 'specialty': 'Unknown', 'role': 'unknown'})
    
    if request.method == 'POST':
        # Just redirect as if the save was successful
        messages.success(request, f"Informations de {staff_member['first_name']} {staff_member['last_name']} mises à jour.")
        return redirect('accounts:staff_detail', pk=pk)
    
    return render(request, 'accounts/staff_edit.html', {'staff': staff_member})

@login_required
def staff_create(request):
    """Create a new staff member"""
    if request.method == 'POST':
        # Just redirect as if the creation was successful
        messages.success(request, "Nouveau membre du personnel ajouté avec succès.")
        return redirect('accounts:staff_list')
    
    return render(request, 'accounts/staff_create.html')
