from django.conf import settings
from django.db import models

from core.models import TimeStampedModel
from dogs.models import Dog


class AdoptionReservation(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
        CANCELLED = 'CANCELLED', 'Cancelled'
        COMPLETED = 'COMPLETED', 'Completed'

    dog = models.ForeignKey(Dog, on_delete=models.CASCADE, related_name='adoption_reservations')
    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='adoption_requests'
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    reservation_date = models.DateField(null=True, blank=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    eligibility_notified_at = models.DateTimeField(null=True, blank=True)
    appointment_schedule = models.DateTimeField(null=True, blank=True)
    staff_notes = models.TextField(blank=True)

    def __str__(self) -> str:
        return f"Adoption {self.pk} - {self.get_status_display()}"


class ReclaimRequest(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
        COMPLETED = 'COMPLETED', 'Completed'

    dog = models.ForeignKey(Dog, on_delete=models.CASCADE, related_name='reclaim_requests')
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reclaim_requests'
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reclaim_approvals',
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    ownership_proof = models.FileField(upload_to='reclaim_proofs/', blank=True)
    staff_notes = models.TextField(blank=True)

    def __str__(self) -> str:
        return f"Reclaim {self.pk} - {self.get_status_display()}"
