from django.db import models

class UserVerification(models.Model):
    USER_TYPE_CHOICES = [
        ('student', 'Student'),
        ('employee', 'Employee'),
    ]
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
    name = models.CharField(max_length=255)
    email = models.EmailField()
    contact = models.CharField(max_length=20)
    college_name = models.CharField(max_length=255, blank=True, null=True)
    college_id = models.CharField(max_length=255, blank=True, null=True)
    government_id = models.CharField(max_length=255)
    verification_status = models.CharField(max_length=20, default='pending')
    upload_time = models.DateTimeField(auto_now_add=True)

    college_id_photo = models.FileField(upload_to='uploads/')
    gov_id_photo = models.FileField(upload_to='uploads/')
    selfie = models.ImageField(upload_to='uploads/')
    ssc_certificate = models.FileField(upload_to='uploads/')
    graduate_certificate = models.FileField(upload_to='uploads/', blank=True, null=True)

    # Extracted fields (optional, can be useful for admin/auditing)
    college_id_name_extracted = models.CharField(max_length=255, blank=True, null=True)
    college_id_num_extracted = models.CharField(max_length=255, blank=True, null=True)
    gov_name_extracted = models.CharField(max_length=255, blank=True, null=True)
    gov_id_extracted = models.CharField(max_length=255, blank=True, null=True)
    gov_dob_extracted = models.CharField(max_length=50, blank=True, null=True)
    ssc_name_extracted = models.CharField(max_length=255, blank=True, null=True)
    ssc_dob_extracted = models.CharField(max_length=50, blank=True, null=True)
    grad_name_extracted = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.user_type.capitalize()}) - {self.verification_status}"

class College(models.Model):
    name = models.CharField(max_length=255, unique=True)
    # Add other relevant fields like country, etc. if needed

    def __str__(self):
        return self.name