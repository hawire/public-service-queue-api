from django.db import models

class Ticket(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('serving', 'Serving'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    citizen = models.ForeignKey(
        'citizens.Citizen',
        on_delete=models.CASCADE,
        related_name='tickets'
    )

    service = models.ForeignKey(
        'services.Service',
        on_delete=models.CASCADE,
        related_name='tickets'
    )

    queue_number = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Ticket {self.queue_number}"
