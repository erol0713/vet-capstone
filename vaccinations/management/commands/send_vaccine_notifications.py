from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.urls import reverse

from notifications.models import Notification
from vaccinations.models import VaccinationRecord


class Command(BaseCommand):
    help = "Send vaccine expiration notifications."

    def handle(self, *args, **options):
        today = timezone.localdate()
        three_days = today + timedelta(days=3)

        expiring = VaccinationRecord.objects.filter(
            expiration_date=three_days,
            notified_three_days=False,
            dog__owner__isnull=False,
        )
        for record in expiring:
            Notification.objects.create(
                user=record.dog.owner,
                title="Vaccine Expiration Reminder",
                message=(
                    f"Your dog's {record.vaccine_type} vaccine will expire on "
                    f"{record.expiration_date}."
                ),
                action_url=reverse('profile'),
            )
            record.notified_three_days = True
            record.save(update_fields=['notified_three_days'])

        expires_today = VaccinationRecord.objects.filter(
            expiration_date=today,
            notified_on_expiry=False,
            dog__owner__isnull=False,
        )
        for record in expires_today:
            Notification.objects.create(
                user=record.dog.owner,
                title="Vaccine Expired",
                message=(
                    f"Your dog's {record.vaccine_type} vaccine expires today "
                    f"({record.expiration_date})."
                ),
                action_url=reverse('profile'),
            )
            record.notified_on_expiry = True
            record.save(update_fields=['notified_on_expiry'])

        self.stdout.write(self.style.SUCCESS("Vaccine notifications processed."))
