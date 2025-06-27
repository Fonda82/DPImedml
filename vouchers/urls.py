from django.urls import path
from . import views

app_name = 'vouchers'
 
urlpatterns = [
    path('', views.voucher_list, name='list'),
    path('create/', views.voucher_create, name='create'),
    path('<int:pk>/', views.voucher_detail, name='detail'),
] 