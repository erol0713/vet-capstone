from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.urls import reverse
from django.utils import timezone

from dogs.models import Dog
from notifications.models import Notification
from vaccinations.models import VaccinationRecord


def create_owner():
    User = get_user_model()
    return User.objects.create_user(
        username='owner@example.com',
        email='owner@example.com',
        password='StrongPass123!',
        role='OWNER',
        email_verified=True,
        is_verified=True,
        legal_consent=True,
    )


def test_send_vaccine_notifications_sends_three_day_reminder():
    owner = create_owner()
    dog = Dog.objects.create(
        name='ReminderDog',
        owner=owner,
        status=Dog.Status.RELEASED,
    )
    record = VaccinationRecord.objects.create(
        dog=dog,
        vaccine_type='Anti-rabies',
        vaccinated_date=timezone.localdate() - timedelta(days=20),
        expiration_date=timezone.localdate() + timedelta(days=3),
    )

    call_command('send_vaccine_notifications')

    record.refresh_from_db()
    notification = Notification.objects.get(user=owner, title='Vaccine Expiration Reminder')
    assert record.notified_three_days is True
    assert notification.action_url == reverse('dogs_owner_detail', kwargs={'pk': dog.pk})


def test_send_vaccine_notifications_sends_today_expiry_notice():
    owner = create_owner()
    dog = Dog.objects.create(
        name='TodayDog',
        owner=owner,
        status=Dog.Status.RELEASED,
    )
    record = VaccinationRecord.objects.create(
        dog=dog,
        vaccine_type='Anti-rabies',
        vaccinated_date=timezone.localdate() - timedelta(days=365),
        expiration_date=timezone.localdate(),
    )

    call_command('send_vaccine_notifications')

    record.refresh_from_db()
    notification = Notification.objects.get(user=owner, title='Vaccine Expired')
    assert record.notified_on_expiry is True
    assert 'expires today' in notification.message.lower()


def test_send_vaccine_notifications_sends_expired_prompt_once():
    owner = create_owner()
    dog = Dog.objects.create(
        name='ExpiredDog',
        owner=owner,
        status=Dog.Status.RELEASED,
    )
    record = VaccinationRecord.objects.create(
        dog=dog,
        vaccine_type='Anti-rabies',
        vaccinated_date=timezone.localdate() - timedelta(days=500),
        expiration_date=timezone.localdate() - timedelta(days=2),
    )

    call_command('send_vaccine_notifications')
    call_command('send_vaccine_notifications')

    record.refresh_from_db()
    assert record.notified_on_expiry is True
    assert Notification.objects.filter(user=owner, title='Vaccination Expired').count() == 1
