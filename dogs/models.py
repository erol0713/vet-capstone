from django.conf import settings
from django.db import models

from core.models import TimeStampedModel


class Dog(TimeStampedModel):
    class VaccinationStatus(models.TextChoices):
        VACCINATED = 'VACCINATED', 'Vaccinated'
        UNVACCINATED = 'UNVACCINATED', 'Unvaccinated'

    class Status(models.TextChoices):
        IMPOUNDED = 'IMPOUNDED', 'Impounded'
        AVAILABLE = 'AVAILABLE', 'Available for Adoption'
        ADOPTED = 'ADOPTED', 'Adopted'
        RECLAIMED = 'RECLAIMED', 'Reclaimed'
        RELEASED = 'RELEASED', 'Released'

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='dogs',
    )
    name = models.CharField(max_length=120, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.IMPOUNDED)
    sex = models.CharField(max_length=10, blank=True)
    age_estimate = models.CharField(max_length=50, blank=True)
    color = models.CharField(max_length=80, blank=True)
    capture_datetime = models.DateTimeField(null=True, blank=True)
    surrender_datetime = models.DateTimeField(null=True, blank=True)
    barangay = models.CharField(max_length=120, blank=True)
    gps_coordinates = models.CharField(max_length=120, blank=True)
    kennel_slot = models.CharField(max_length=30, blank=True)
    photo = models.ImageField(upload_to='dogs/', blank=True)
    notes = models.TextField(blank=True)
    vaccination_status = models.CharField(
        max_length=20,
        choices=VaccinationStatus.choices,
        blank=True,
        default='',
    )
    vaccination_proof = models.FileField(upload_to='vaccination_proofs/', blank=True)
    vaccination_request = models.BooleanField(default=False)
    vaccination_schedule = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return f"Dog #{self.pk} - {self.get_status_display()}"
