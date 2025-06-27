from django.urls import path
from . import views

app_name = 'rehabilitation'
 
urlpatterns = [
    path('', views.rehabilitation_list, name='list'),
    path('<int:pk>/', views.rehabilitation_detail, name='detail'),
    path('create/', views.rehabilitation_create_select_patient, name='create_select_patient'),
    path('create/<int:patient_id>/', views.rehabilitation_create, name='create'),
    path('session/create/<int:plan_id>/', views.session_create, name='session_create'),
    path('patient-exercises/', views.patient_exercises, name='patient_exercises'),
] 