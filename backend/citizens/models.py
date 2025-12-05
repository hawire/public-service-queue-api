from django.db import models

class Citizen(models.Model):
    full_name = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=15)
    national_id = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name
