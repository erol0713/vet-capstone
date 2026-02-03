from django.contrib.auth import get_user_model
from django.utils import timezone

from dogs.models import Dog


def create_owner(email='owner@example.com', verified=True):
    User = get_user_model()
    return User.objects.create_user(
        username=email,
        email=email,
        password='StrongPass123!',
        role='OWNER',
        email_verified=verified,
        is_verified=verified,
        legal_consent=True,
    )


def test_owner_can_delete_registered_dog(client):
    owner = create_owner()
    dog = Dog.objects.create(name='HomeDog', owner=owner, status=Dog.Status.RELEASED)
    client.force_login(owner)

    response = client.post(f'/dogs/{dog.id}/delete/')

    assert response.status_code == 302
    assert not Dog.objects.filter(id=dog.id).exists()


def test_owner_cannot_delete_pound_dog(client):
    owner = create_owner()
    dog = Dog.objects.create(
        name='PoundDog',
        owner=owner,
        status=Dog.Status.IMPOUNDED,
        capture_datetime=timezone.now(),
    )
    client.force_login(owner)

    response = client.post(f'/dogs/{dog.id}/delete/')

    assert response.status_code == 404
    assert Dog.objects.filter(id=dog.id).exists()


def test_other_user_cannot_delete_dog(client):
    owner = create_owner('owner@example.com')
    other = create_owner('other@example.com')
    dog = Dog.objects.create(name='HomeDog', owner=owner, status=Dog.Status.RELEASED)
    client.force_login(other)

    response = client.post(f'/dogs/{dog.id}/delete/')

    assert response.status_code == 404
    assert Dog.objects.filter(id=dog.id).exists()
