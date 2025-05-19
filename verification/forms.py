from django import forms
from .models import UserVerification, College

class UserVerificationForm(forms.ModelForm):
    class Meta:
        model = UserVerification
        fields = [
            'user_type',
            'name',
            'email',
            'contact',
            'college_name',
            'college_id',
            'government_id',
            'college_id_photo',
            'gov_id_photo',
            'selfie',
            'ssc_certificate',
            'graduate_certificate',
        ]
        widgets = {
            'user_type': forms.Select(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'contact': forms.TextInput(attrs={'class': 'form-control'}),
            'college_name': forms.TextInput(attrs={'class': 'form-control'}),
            'college_id': forms.TextInput(attrs={'class': 'form-control'}),
            'government_id': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        user_type = cleaned_data.get("user_type")
        college_name = cleaned_data.get("college_name")
        college_id = cleaned_data.get("college_id")
        graduate_certificate = cleaned_data.get("graduate_certificate")

        if user_type == "student":
            if not college_name:
                self.add_error('college_name', 'College name is required for students.')
            if not college_id:
                self.add_error('college_id', 'College ID is required for students.')

        elif user_type == "employee":
            if not graduate_certificate:
                self.add_error('graduate_certificate', 'Graduate certificate is required for employees.')

        return cleaned_data
