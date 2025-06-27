from django.urls import path
from . import views

app_name = 'referrals'

urlpatterns = [
    path('', views.referral_list, name='list'),
    path('create/', views.referral_create, name='create'),
    path('<int:pk>/', views.referral_detail, name='detail'),
    path('<int:pk>/respond/', views.referral_respond, name='respond'),
    path('select-patient/', views.select_patient, name='select_patient'),
] 