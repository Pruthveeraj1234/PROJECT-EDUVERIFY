from django import forms
from .models import UserVerification

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
            'digilocker_govt_doc_id',
            'digilocker_ssc_doc_id',
            'ssc_certificate',
            'graduate_certificate',
            'selfie',
        ]
        widgets = {
            'user_type': forms.Select(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'contact': forms.TextInput(attrs={'class': 'form-control'}),
            'college_name': forms.TextInput(attrs={'class': 'form-control'}),
            'college_id': forms.TextInput(attrs={'class': 'form-control'}),
            'digilocker_govt_doc_id': forms.TextInput(attrs={'class': 'form-control'}),
            'digilocker_ssc_doc_id': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        user_type = cleaned_data.get("user_type")
        college_name = cleaned_data.get("college_name")
        college_id = cleaned_data.get("college_id")
        graduate_certificate = cleaned_data.get("graduate_certificate")
        digilocker_ssc_doc_id = cleaned_data.get("digilocker_ssc_doc_id")
        ssc_certificate = cleaned_data.get("ssc_certificate")

        if user_type == "student":
            if not college_name:
                self.add_error('college_name', 'College name is required for students.')
            if not college_id:
                self.add_error('college_id', 'College ID is required for students.')

        if user_type == "employee" and not graduate_certificate:
            self.add_error('graduate_certificate', 'Graduate certificate is required for employees.')

        if not digilocker_ssc_doc_id and not ssc_certificate:
            self.add_error('ssc_certificate', 'SSC certificate or DigiLocker document ID is required.')

        return cleaned_data
