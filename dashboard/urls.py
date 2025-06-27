from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.index, name='index'),
    path('superadmin/', views.superadmin_dashboard, name='superadmin'),
    path('facility-admin/', views.facility_admin_dashboard, name='facility_admin'),
    path('doctor/', views.doctor_dashboard, name='doctor'),
    path('patient/', views.patient_dashboard, name='patient'),
    
    # Security and Compliance URLs
    path('security/', views.security_dashboard, name='security'),
    path('gdpr/', views.gdpr_compliance, name='gdpr'),
    path('patient/<int:patient_id>/export/', views.patient_data_export, name='patient_data_export'),
    path('patient/<int:patient_id>/consent/', views.patient_consent_management, name='patient_consent'),
] 