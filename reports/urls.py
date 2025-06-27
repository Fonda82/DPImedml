from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('system/', views.system_report, name='system'),
] 