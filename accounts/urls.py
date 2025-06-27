from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_demo, name='login'),
    path('logout/', views.logout_demo, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('switch-role/<str:role>/', views.switch_role, name='switch_role'),
    path('user/create/', views.user_create, name='user_create'),
    
    # Staff related URLs
    path('staff/', views.staff_list, name='staff_list'),
    path('staff/<int:pk>/', views.staff_detail, name='staff_detail'),
    path('staff/<int:pk>/edit/', views.staff_edit, name='staff_edit'),
    path('staff/create/', views.staff_create, name='staff_create'),
    
    # A general create view for other models if needed, pointing to a placeholder
    # This resolves the immediate 'create' error, but should be pointed to a
    # specific create view for patients, vouchers etc. as you build them out.
    path('create/', views.user_create, name='user_create'),
] 