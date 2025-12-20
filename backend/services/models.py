from django.db import models

class Service(models.Model):
    name = models.CharField(max_length=150)
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
