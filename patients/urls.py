from django.urls import path
from . import views

app_name = 'patients'
 
urlpatterns = [
    path('', views.patient_list, name='list'),
    path('create/', views.patient_create, name='create'),
    path('<int:pk>/', views.patient_detail, name='detail'),
    path('<int:pk>/edit/', views.patient_edit, name='edit'),
    path('<int:pk>/medical-history/', views.medical_history, name='medical_history'),
    path('medical-record/<int:pk>/', views.medical_record, name='medical_record'),
    path('<int:pk>/documents/', views.patient_documents, name='documents'),
    path('<int:pk>/documents/add/', views.add_document, name='add_document'),
    path('<int:pk>/medical-profile/', views.medical_profile, name='medical_profile'),
    # ICD-10 Professional Medical Coding
    path('icd10-search/', views.icd10_search, name='icd10_search'),
    path('<int:patient_id>/medical-record/create/', views.medical_record_create, name='medical_record_create'),
    # Vital Signs Dashboard
    path('<int:pk>/vital-signs/', views.vital_signs_dashboard, name='vital_signs_dashboard'),
    path('<int:pk>/vital-signs/trends/', views.vital_signs_trends, name='vital_signs_trends'),
    path('<int:pk>/vital-signs/growth-chart/', views.growth_chart, name='growth_chart'),
    path('<int:pk>/vital-signs/api/', views.vital_signs_api, name='vital_signs_api'),
    # Hospitalization Management
    path('hospitalizations/', views.hospitalization_list, name='hospitalizations'),
    path('hospitalizations/create/', views.hospitalization_create, name='hospitalization_create'),
    path('hospitalizations/<int:pk>/', views.hospitalization_detail, name='hospitalization_detail'),
    path('hospitalizations/<int:pk>/add-note/', views.add_progress_note, name='add_progress_note'),
] 