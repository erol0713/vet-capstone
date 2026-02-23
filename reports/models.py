from django.conf import settings
from django.db import models

from core.models import TimeStampedModel


class Report(TimeStampedModel):
    class ReportType(models.TextChoices):
        STRAY = 'STRAY', 'Stray Dog'
        INJURED = 'INJURED', 'Injured Dog'
        SURRENDER = 'SURRENDER', 'Surrender Dog'
        DANGEROUS = 'DANGEROUS', 'Dangerous Dog'
        BITE_INCIDENT = 'BITE_INCIDENT', 'Bite Incident'
        ABANDONED = 'ABANDONED', 'Abandoned Dog'
        WELFARE = 'WELFARE', 'Welfare Concern'
        OTHER = 'OTHER', 'Other'

    class LocationMethod(models.TextChoices):
        GOOGLE_MAPS = 'GOOGLE_MAPS', 'Google Maps'
        MANUAL_ADDRESS = 'MANUAL_ADDRESS', 'Manual Address'
        BOTH = 'BOTH', 'Google Maps + Manual Address'

    class Status(models.TextChoices):
        OPEN = 'OPEN', 'Open'
        IN_REVIEW = 'IN_REVIEW', 'In Review'
        RESOLVED = 'RESOLVED', 'Resolved'
        CLOSED = 'CLOSED', 'Closed'

    report_type = models.CharField(max_length=20, choices=ReportType.choices)
    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reports'
    )
    location = models.CharField(max_length=255)
    photo = models.FileField(upload_to='reports/', blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    notes = models.TextField(blank=True)
    contact_name = models.CharField(max_length=120, blank=True)
    contact_phone = models.CharField(max_length=40, blank=True)
    contact_email = models.EmailField(blank=True)
    description = models.TextField(blank=True)
    location_method = models.CharField(
        max_length=20,
        choices=LocationMethod.choices,
        blank=True,
    )
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    maps_url = models.URLField(max_length=500, blank=True)
    address_json = models.JSONField(null=True, blank=True)

    def __str__(self) -> str:
        return f"Report {self.pk} - {self.get_report_type_display()}"
