from django.contrib import admin
from .models import UserVerification, College

@admin.register(UserVerification)
class UserVerificationAdmin(admin.ModelAdmin):
    list_display = ('name', 'user_type', 'email', 'verification_status', 'upload_time')
    list_filter = ('user_type', 'verification_status')
    search_fields = ('name', 'email', 'government_id')
    readonly_fields = ('upload_time',)
    # Add more configurations as needed

@admin.register(College)
class CollegeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    # Add more configurations as needed