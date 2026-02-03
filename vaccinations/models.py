from django.db import models

from core.models import TimeStampedModel
from dogs.models import Dog


class VaccinationRecord(TimeStampedModel):
    dog = models.ForeignKey(Dog, on_delete=models.CASCADE, related_name='vaccinations')
    vaccine_type = models.CharField(max_length=120)
    vaccinated_date = models.DateField()
    expiration_date = models.DateField(null=True, blank=True)
    notified_three_days = models.BooleanField(default=False)
    notified_on_expiry = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"{self.vaccine_type} for Dog #{self.dog_id}"
