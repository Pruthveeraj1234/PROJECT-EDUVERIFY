from django.db import models


class College(models.Model):
    name = models.CharField(max_length=255, unique=True)
    country = models.CharField(max_length=100, blank=True, null=True)  # Optional for future use

    def __str__(self):
        return self.name


class UserVerification(models.Model):
    USER_TYPE_CHOICES = [
        ('student', 'Student'),
        ('employee', 'Employee'),
    ]

    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
    name = models.CharField(max_length=255)
    email = models.EmailField()
    contact = models.CharField(max_length=20)

    # College info
    college_name = models.CharField(max_length=255, blank=True, null=True)
    college = models.ForeignKey(College, on_delete=models.SET_NULL, null=True, blank=True)

    # Government ID info
    government_id = models.CharField(max_length=255)
    govt_id_from_digilocker = models.BooleanField(default=True)
    digilocker_govt_doc_id = models.CharField(max_length=255, blank=True, null=True)

    # SSC Certificate info
    ssc_certificate = models.FileField(upload_to='uploads/', blank=True, null=True)
    ssc_certificate_from_digilocker = models.BooleanField(default=False)
    digilocker_ssc_doc_id = models.CharField(max_length=255, blank=True, null=True)

    # Other uploads
    college_id_photo = models.FileField(upload_to='uploads/')
    selfie = models.ImageField(upload_to='uploads/')
    graduate_certificate = models.FileField(upload_to='uploads/', blank=True, null=True)

    # Verification status
    verification_status = models.CharField(max_length=20, default='pending')
    upload_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.user_type.capitalize()}) - {self.verification_status}"
