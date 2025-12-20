from django.db import models
from django.utils import timezone

class Ticket(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("serving", "Serving"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    citizen = models.ForeignKey(
        "citizens.Citizen",
        on_delete=models.CASCADE,
        related_name="tickets"
    )
    service = models.ForeignKey(
        "services.Service",
        on_delete=models.CASCADE,
        related_name="tickets"
    )
    number = models.PositiveIntegerField(null=True, blank=True)  # auto-assigned per service per day
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.number:
            # Assign next sequential number for this service today
            today = timezone.now().date()
            last_ticket = Ticket.objects.filter(
                service=self.service,
                created_at__date=today
            ).order_by('-number').first()
            self.number = 1 if not last_ticket else last_ticket.number + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Ticket #{self.number} - {self.service.name}"
