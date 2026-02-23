from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db.models import Sum
from django.utils import timezone

from adoption.models import AdoptionReservation
from adoption.views import (
    RECLAIM_WINDOW_DAYS,
    has_active_reclaim,
    notify_reservation_eligibility,
    reclaim_window_elapsed,
)
from dogs.models import Dog
from penalties.models import PenaltyCase, PenaltyLineItem

DAILY_LODGING_FEE = Decimal('500.00')
LODGING_DESCRIPTION = 'Lodging Fee'


class Command(BaseCommand):
    help = (
        'Mark eligible dogs as available, notify adoption reservations, and apply '
        'daily lodging penalties after the reclaim window.'
    )

    def handle(self, *args, **options):
        now = timezone.now()
        today = timezone.localdate()

        updated_dogs = 0
        eligible_dogs = Dog.objects.filter(
            status=Dog.Status.IMPOUNDED,
            capture_datetime__isnull=False,
        )
        for dog in eligible_dogs:
            if not reclaim_window_elapsed(dog, now=now):
                continue
            if has_active_reclaim(dog):
                continue
            dog.status = Dog.Status.AVAILABLE
            dog.save(update_fields=['status'])
            updated_dogs += 1

        pending_reservations = AdoptionReservation.objects.select_related('dog', 'requester').filter(
            status=AdoptionReservation.Status.PENDING
        )
        notify_reservation_eligibility(pending_reservations)

        updated_cases = 0
        cases = (
            PenaltyCase.objects.select_related('dog')
            .filter(
                is_finalized=False,
                reclaimed_at__isnull=True,
                dog__capture_datetime__isnull=False,
            )
            .order_by('id')
        )
        for case in cases:
            capture_dt = case.dog.capture_datetime
            capture_date = (
                timezone.localtime(capture_dt).date()
                if timezone.is_aware(capture_dt)
                else capture_dt.date()
            )
            days_since_capture = (today - capture_date).days
            days_overdue = days_since_capture - RECLAIM_WINDOW_DAYS
            if days_overdue <= 0:
                continue

            line = case.line_items.filter(description=LODGING_DESCRIPTION).first()
            if not line:
                PenaltyLineItem.objects.create(
                    case=case,
                    description=LODGING_DESCRIPTION,
                    quantity=days_overdue,
                    unit_amount=DAILY_LODGING_FEE,
                    total=DAILY_LODGING_FEE * days_overdue,
                )
            else:
                if line.quantity != days_overdue or line.unit_amount != DAILY_LODGING_FEE:
                    line.quantity = days_overdue
                    line.unit_amount = DAILY_LODGING_FEE
                    line.save()

            total = (
                case.line_items.aggregate(total=Sum('total')).get('total') or Decimal('0.00')
            )
            if case.total_amount != total:
                case.total_amount = total
                case.save(update_fields=['total_amount'])
            updated_cases += 1

        self.stdout.write(
            self.style.SUCCESS(
                'Reclaim window processed: '
                f'{updated_dogs} dogs updated, {updated_cases} penalty cases recalculated.'
            )
        )
