from django.conf import settings
from django.db import models

from core.models import TimeStampedModel


class Report(TimeStampedModel):
    class ReportType(models.TextChoices):
        STRAY = 'STRAY', 'Stray'
        SURRENDER = 'SURRENDER', 'Surrender'

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
    description = models.TextField(blank=True)

    def __str__(self) -> str:
        return f"Report {self.pk} - {self.get_report_type_display()}"
