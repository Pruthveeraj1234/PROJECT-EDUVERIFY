from django.urls import path
from . import views

urlpatterns = [
    path('verify/', views.verify, name='verify'),
    path('verify/digilocker/', views.verify_digilocker, name='verify_digilocker'),
    path('verify/manual/', views.verify_manual, name='verify_manual'),
    path('verify/ssc-manual/', views.verify_ssc_manual, name='verify_ssc_manual'),
    path('digilocker/callback/', views.digilocker_callback, name='digilocker_callback'),
]
