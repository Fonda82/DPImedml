from django.urls import path
from . import views

app_name = 'prescriptions'

urlpatterns = [
    # Prescription Management
    path('', views.prescription_list, name='list'),
    path('<int:pk>/', views.prescription_detail, name='detail'),
    path('create/', views.prescription_create, name='create'),
    path('create/patient/<int:patient_id>/', views.prescription_create_for_patient, name='create_for_patient'),
    path('<int:pk>/edit/', views.prescription_edit, name='edit'),
    path('<int:pk>/validate/', views.prescription_validate, name='validate'),
    path('<int:pk>/dispense/', views.prescription_dispense, name='dispense'),
    path('<int:pk>/cancel/', views.prescription_cancel, name='cancel'),
    path('<int:pk>/print/', views.prescription_print, name='print'),
    
    # Medication Management
    path('medications/', views.medication_list, name='medication_list'),
    path('medications/<int:pk>/', views.medication_detail, name='medication_detail'),
    path('medications/search/', views.medication_search, name='medication_search'),
    
    # Templates
    path('templates/', views.template_list, name='template_list'),
    path('templates/<int:pk>/', views.template_detail, name='template_detail'),
    path('templates/<int:pk>/apply/<int:patient_id>/', views.apply_template, name='apply_template'),
    
    # Dashboard and Reports
    path('dashboard/', views.prescription_dashboard, name='dashboard'),
    path('reports/', views.prescription_reports, name='reports'),
    
    # API Endpoints
    path('api/medication-dose/', views.calculate_medication_dose, name='calculate_dose'),
    path('api/drug-interactions/', views.check_drug_interactions, name='check_interactions'),
] 