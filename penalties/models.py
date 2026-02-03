from decimal import Decimal

from django.conf import settings
from django.db import models

from core.models import TimeStampedModel
from dogs.models import Dog


class PenaltyCase(TimeStampedModel):
    dog = models.ForeignKey(Dog, on_delete=models.CASCADE, related_name='penalty_cases')
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='penalty_cases'
    )
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    reclaimed_at = models.DateTimeField(null=True, blank=True)
    is_finalized = models.BooleanField(default=False)
    finalized_at = models.DateTimeField(null=True, blank=True)
    locked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='finalized_penalties',
    )

    def __str__(self) -> str:
        return f"PenaltyCase {self.pk} - {self.owner.username}"


class PenaltyLineItem(TimeStampedModel):
    case = models.ForeignKey(PenaltyCase, on_delete=models.CASCADE, related_name='line_items')
    checklist_item = models.ForeignKey(
        'PenaltyChecklistItem',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='line_items',
    )
    description = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField(default=1)
    unit_amount = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs) -> None:
        self.total = self.unit_amount * self.quantity
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.description} ({self.quantity}x)"


class PenaltyChecklistItem(models.Model):
    class Section(models.TextChoices):
        SECTION_28 = 'SECTION_28', 'Section 28'
        SECTION_29 = 'SECTION_29', 'Section 29'
        ADDITIONAL = 'ADDITIONAL', 'Additional'

    code = models.CharField(max_length=30, unique=True)
    section = models.CharField(max_length=20, choices=Section.choices)
    description = models.CharField(max_length=255)
    default_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.description
