from django.urls import path
from . import views

urlpatterns = [
    path('verify/', views.verify, name='verify'),
    # Add other URLs for potential future views
]