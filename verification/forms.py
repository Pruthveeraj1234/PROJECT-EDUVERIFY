from django import forms

class VerificationForm(forms.Form):
    user_type = forms.ChoiceField(choices=[('student', 'Student'), ('employee', 'Employee')])
    name = forms.CharField(max_length=255)
    email = forms.EmailField()
    contact = forms.CharField(max_length=20)
    college_name = forms.CharField(max_length=255, required=False)
    college_id = forms.CharField(max_length=255, required=False)
    government_id = forms.CharField(max_length=255)
    college_id_photo = forms.FileField(required=True)
    gov_id_photo = forms.FileField(required=True)
    selfie = forms.ImageField(required=True)
    ssc_certificate = forms.FileField(required=True)
    graduate_certificate = forms.FileField(required=False)

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