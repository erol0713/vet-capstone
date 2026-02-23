from django.contrib.auth import get_user_model
from django.urls import reverse

from notifications.models import Notification
from vaccinations.models import VaccinationRecord

from .models import Dog


def apply_intake_status(dog: Dog) -> None:
    if dog.capture_datetime or dog.surrender_datetime or not dog.owner:
        if dog.surrender_datetime:
            dog.status = Dog.Status.AVAILABLE
        else:
            dog.status = Dog.Status.IMPOUNDED


def latest_vaccination_record(dog: Dog) -> VaccinationRecord | None:
    latest_with_expiration = (
        dog.vaccinations.filter(expiration_date__isnull=False)
        .order_by('-expiration_date', '-created_at')
        .first()
    )
    if latest_with_expiration:
        return latest_with_expiration
    return dog.vaccinations.order_by('-created_at').first()


def notify_vaccination_staff(title: str, message: str) -> None:
    User = get_user_model()
    recipients = User.objects.filter(role__in=['ADMIN', 'STAFF'])
    if not recipients.exists():
        return
    queue_url = reverse('dogs_vaccination_requests')
    Notification.objects.bulk_create(
        [
            Notification(user=user, title=title, message=message, action_url=queue_url)
            for user in recipients
        ]
    )
