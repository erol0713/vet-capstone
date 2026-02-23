from django.db import models
from django.utils import timezone

from core.models import TimeStampedModel
from dogs.models import Dog


class VaccinationRecord(TimeStampedModel):
    dog = models.ForeignKey(Dog, on_delete=models.CASCADE, related_name='vaccinations')
    vaccine_type = models.CharField(max_length=120, blank=True, default='General Vaccine')
    vaccinated_date = models.DateField(null=True, blank=True)
    expiration_date = models.DateField(null=True, blank=True)
    from_owner_proof = models.BooleanField(default=False)
    notified_three_days = models.BooleanField(default=False)
    notified_on_expiry = models.BooleanField(default=False)

    @property
    def is_expired(self) -> bool:
        return bool(self.expiration_date and self.expiration_date < timezone.localdate())

    def __str__(self) -> str:
        return f"{self.vaccine_type or 'Vaccine'} for Dog #{self.dog_id}"
