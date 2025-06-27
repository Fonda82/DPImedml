from django.urls import path
from . import views

app_name = 'facilities'
 
urlpatterns = [
    path('', views.facility_list, name='list'),
    path('create/', views.facility_create, name='create'),
    path('<int:pk>/', views.facility_detail, name='detail'),
    path('<int:pk>/edit/', views.facility_edit, name='edit'),
    
    # Communication URLs
    path('communications/', views.communication_list, name='communications'),
    path('communications/create/', views.communication_create, name='communication_create'),
    path('communications/<int:pk>/', views.communication_detail, name='communication_detail'),
    path('communications/<int:pk>/respond/', views.communication_respond, name='communication_respond'),
] 