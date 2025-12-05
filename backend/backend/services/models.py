from django.db import models

class Service(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    estimated_duration = models.PositiveIntegerField()  # in minutes
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
