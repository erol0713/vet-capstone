from django.contrib.auth import get_user_model
from django.utils import timezone

from notifications.models import Notification
from penalties.models import PenaltyCase

from adoption.models import AdoptionReservation, ReclaimRequest
from dogs.models import Dog


def create_user(role, verified=True):
    User = get_user_model()
    return User.objects.create_user(
        username=f'{role.lower()}@example.com',
        email=f'{role.lower()}@example.com',
        password='StrongPass123!',
        role=role,
        email_verified=verified,
        is_verified=verified,
        legal_consent=True,
    )


def test_verified_user_can_reserve(client):
    user = create_user('OWNER', verified=True)
    dog = Dog.objects.create(status=Dog.Status.AVAILABLE)
    client.force_login(user)

    response = client.post(f'/adoption/dogs/{dog.id}/reserve/', {'reservation_date': '2026-02-01'})

    assert response.status_code == 302
    assert AdoptionReservation.objects.filter(dog=dog, requester=user).exists()


def test_unverified_user_blocked_from_reserve(client):
    user = create_user('OWNER', verified=False)
    dog = Dog.objects.create(status=Dog.Status.AVAILABLE)
    client.force_login(user)

    response = client.get(f'/adoption/dogs/{dog.id}/reserve/', follow=True)

    assert response.status_code == 200
    assert b'verification' in response.content.lower()


def test_staff_can_complete_adoption(client):
    staff = create_user('STAFF', verified=True)
    dog = Dog.objects.create(status=Dog.Status.AVAILABLE)
    reservation = AdoptionReservation.objects.create(dog=dog, requester=staff)
    client.force_login(staff)

    response = client.get(f'/staff/adoption/{reservation.id}/status/COMPLETED/', follow=True)

    dog.refresh_from_db()
    assert response.status_code == 200
    assert dog.status == Dog.Status.ADOPTED


def test_staff_can_complete_reclaim(client):
    staff = create_user('STAFF', verified=True)
    dog = Dog.objects.create(status=Dog.Status.IMPOUNDED)
    reclaim = ReclaimRequest.objects.create(dog=dog, owner=staff)
    client.force_login(staff)

    response = client.get(f'/staff/reclaim/{reclaim.id}/status/COMPLETED/', follow=True)

    dog.refresh_from_db()
    assert response.status_code == 200
    assert dog.status == Dog.Status.RECLAIMED
    assert dog.owner == staff
    assert PenaltyCase.objects.filter(dog=dog, owner=staff).exists()


def test_verified_user_can_request_reclaim_for_available_captured_dog(client):
    user = create_user('OWNER', verified=True)
    dog = Dog.objects.create(status=Dog.Status.AVAILABLE, capture_datetime=timezone.now())
    client.force_login(user)

    response = client.post(
        f'/adoption/dogs/{dog.id}/reclaim/',
        {'reclaim_date': '2026-02-01'},
    )

    assert response.status_code == 302
    assert ReclaimRequest.objects.filter(dog=dog, owner=user).exists()


def test_reclaim_blocked_for_adopted_dog(client):
    user = create_user('OWNER', verified=True)
    dog = Dog.objects.create(status=Dog.Status.ADOPTED, capture_datetime=timezone.now())
    client.force_login(user)

    response = client.get(f'/adoption/dogs/{dog.id}/reclaim/', follow=True)

    assert response.status_code == 200
    assert b'cannot be reclaimed' in response.content.lower()


def test_adoption_request_notifies_staff_and_admin(client):
    admin = create_user('ADMIN', verified=True)
    staff = create_user('STAFF', verified=True)
    owner = create_user('OWNER', verified=True)
    dog = Dog.objects.create(status=Dog.Status.AVAILABLE)
    client.force_login(owner)

    response = client.post(
        f'/adoption/dogs/{dog.id}/reserve/',
        {'reservation_date': '2026-02-01'},
    )

    assert response.status_code == 302
    assert Notification.objects.filter(user=admin, title='New adoption request').exists()
    assert Notification.objects.filter(user=staff, title='New adoption request').exists()


def test_reclaim_request_notifies_staff_and_admin(client):
    admin = create_user('ADMIN', verified=True)
    staff = create_user('STAFF', verified=True)
    owner = create_user('OWNER', verified=True)
    dog = Dog.objects.create(status=Dog.Status.IMPOUNDED, capture_datetime=timezone.now())
    client.force_login(owner)

    response = client.post(
        f'/adoption/dogs/{dog.id}/reclaim/',
        {'reclaim_date': '2026-02-01'},
    )

    assert response.status_code == 302
    assert Notification.objects.filter(user=admin, title='New reclaim request').exists()
    assert Notification.objects.filter(user=staff, title='New reclaim request').exists()
    assert PenaltyCase.objects.filter(dog=dog, owner=owner).exists()
