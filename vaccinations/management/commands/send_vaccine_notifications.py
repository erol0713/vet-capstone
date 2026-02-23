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
            vaccine_name = record.vaccine_type or "vaccine"
            action_url = reverse('dogs_owner_detail', kwargs={'pk': record.dog_id})
            Notification.objects.create(
                user=record.dog.owner,
                title="Vaccine Expiration Reminder",
                message=(
                    f"Your dog's {vaccine_name} vaccine will expire on "
                    f"{record.expiration_date}. Please prepare for renewal scheduling."
                ),
                action_url=action_url,
            )
            record.notified_three_days = True
            record.save(update_fields=['notified_three_days'])

        expires_or_expired = VaccinationRecord.objects.filter(
            expiration_date__lte=today,
            notified_on_expiry=False,
            dog__owner__isnull=False,
        )
        for record in expires_or_expired:
            vaccine_name = record.vaccine_type or "vaccine"
            action_url = reverse('dogs_owner_detail', kwargs={'pk': record.dog_id})
            if record.expiration_date == today:
                title = "Vaccine Expired"
                message = (
                    f"Your dog's {vaccine_name} vaccine expires today "
                    f"({record.expiration_date}). Request a new vaccination schedule if needed."
                )
            else:
                title = "Vaccination Expired"
                message = (
                    f"Your dog's {vaccine_name} vaccine already expired on "
                    f"{record.expiration_date}. Please request a new vaccination schedule."
                )
            Notification.objects.create(
                user=record.dog.owner,
                title=title,
                message=message,
                action_url=action_url,
            )
            record.notified_on_expiry = True
            record.save(update_fields=['notified_on_expiry'])

        self.stdout.write(self.style.SUCCESS("Vaccine notifications processed."))
