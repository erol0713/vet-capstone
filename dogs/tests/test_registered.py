from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from notifications.models import Notification
from dogs.models import Dog
from vaccinations.models import VaccinationRecord


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


def test_vaccinated_requires_proof(client):
    owner = create_owner()
    client.force_login(owner)

    response = client.post(
        '/dogs/register/',
        {
            'name': 'Buddy',
            'vaccination_status': Dog.VaccinationStatus.VACCINATED,
        },
    )

    assert response.status_code == 200
    assert not Dog.objects.filter(name='Buddy').exists()


def test_vaccinated_with_proof_succeeds(client):
    owner = create_owner()
    client.force_login(owner)
    proof = SimpleUploadedFile('proof.pdf', b'proof', content_type='application/pdf')

    response = client.post(
        '/dogs/register/',
        {
            'name': 'Buddy',
            'vaccination_status': Dog.VaccinationStatus.VACCINATED,
            'vaccination_proof': proof,
        },
        follow=True,
    )

    assert response.status_code == 200
    dog = Dog.objects.get(name='Buddy')
    assert dog.vaccination_status == Dog.VaccinationStatus.VACCINATED
    assert dog.vaccination_proof.name


def test_unvaccinated_requires_request(client):
    owner = create_owner()
    client.force_login(owner)

    response = client.post(
        '/dogs/register/',
        {
            'name': 'Lucky',
            'vaccination_status': Dog.VaccinationStatus.UNVACCINATED,
        },
    )

    assert response.status_code == 200
    assert not Dog.objects.filter(name='Lucky').exists()


def test_unvaccinated_with_request_succeeds(client):
    owner = create_owner()
    client.force_login(owner)

    response = client.post(
        '/dogs/register/',
        {
            'name': 'Max',
            'vaccination_status': Dog.VaccinationStatus.UNVACCINATED,
            'vaccination_request': 'on',
        },
        follow=True,
    )

    assert response.status_code == 200
    dog = Dog.objects.get(name='Max')
    assert dog.vaccination_status == Dog.VaccinationStatus.UNVACCINATED
    assert dog.vaccination_request is True


def test_registered_dog_starts_pending_approval(client):
    owner = create_owner()
    client.force_login(owner)
    proof = SimpleUploadedFile('proof.pdf', b'proof', content_type='application/pdf')

    response = client.post(
        '/dogs/register/',
        {
            'name': 'PendingDog',
            'vaccination_status': Dog.VaccinationStatus.VACCINATED,
            'vaccination_proof': proof,
        },
        follow=True,
    )

    dog = Dog.objects.get(name='PendingDog')
    my_dogs_response = client.get('/dogs/my-dogs/')
    assert response.status_code == 200
    assert dog.registration_approval_status == Dog.RegistrationApprovalStatus.PENDING
    assert b'PendingDog' not in my_dogs_response.content


def test_staff_approval_makes_registered_dog_visible_to_owner(client):
    owner = create_owner()
    staff = create_owner('staff@example.com')
    staff.role = 'STAFF'
    staff.save(update_fields=['role'])
    dog = Dog.objects.create(
        name='NeedsApproval',
        owner=owner,
        status=Dog.Status.RELEASED,
        vaccination_status=Dog.VaccinationStatus.VACCINATED,
        vaccination_proof='vaccination_proofs/proof.pdf',
        registration_approval_status=Dog.RegistrationApprovalStatus.PENDING,
    )

    client.force_login(staff)
    approve_response = client.post(
        f'/staff/dogs/registered/{dog.id}/',
        {'action': 'approve'},
        follow=True,
    )

    dog.refresh_from_db()
    client.force_login(owner)
    my_dogs_response = client.get('/dogs/my-dogs/')

    assert approve_response.status_code == 200
    assert dog.registration_approval_status == Dog.RegistrationApprovalStatus.APPROVED
    assert b'NeedsApproval' in my_dogs_response.content


def test_owner_can_view_owned_dog_profile(client):
    owner = create_owner()
    dog = Dog.objects.create(
        name='HomeDog',
        owner=owner,
        status=Dog.Status.RELEASED,
        vaccination_status=Dog.VaccinationStatus.VACCINATED,
        registration_approval_status=Dog.RegistrationApprovalStatus.APPROVED,
    )
    client.force_login(owner)

    response = client.get(f'/dogs/my-dogs/{dog.id}/')

    assert response.status_code == 200
    assert b'HomeDog' in response.content
    assert b'Vaccinated' in response.content


def test_owner_profile_shows_vaccination_and_expiration_dates(client):
    owner = create_owner()
    dog = Dog.objects.create(
        name='RecordDog',
        owner=owner,
        status=Dog.Status.RELEASED,
        vaccination_status=Dog.VaccinationStatus.VACCINATED,
        registration_approval_status=Dog.RegistrationApprovalStatus.APPROVED,
    )
    VaccinationRecord.objects.create(
        dog=dog,
        vaccine_type='Anti-rabies',
        vaccinated_date=timezone.localdate() - timedelta(days=10),
        expiration_date=timezone.localdate() + timedelta(days=355),
    )
    client.force_login(owner)

    response = client.get(f'/dogs/my-dogs/{dog.id}/')

    assert response.status_code == 200
    assert b'Vaccinated Date' in response.content
    assert b'Vaccine Expiration' in response.content


def test_owner_cannot_view_other_owner_dog_profile(client):
    owner = create_owner('owner@example.com')
    other = create_owner('other@example.com')
    dog = Dog.objects.create(
        name='HomeDog',
        owner=owner,
        status=Dog.Status.RELEASED,
        registration_approval_status=Dog.RegistrationApprovalStatus.APPROVED,
    )
    client.force_login(other)

    response = client.get(f'/dogs/my-dogs/{dog.id}/')

    assert response.status_code == 404


def test_anonymous_redirected_from_owner_dog_profile(client):
    owner = create_owner()
    dog = Dog.objects.create(
        name='HomeDog',
        owner=owner,
        status=Dog.Status.RELEASED,
        registration_approval_status=Dog.RegistrationApprovalStatus.APPROVED,
    )

    response = client.get(f'/dogs/my-dogs/{dog.id}/')

    assert response.status_code == 302
    assert '/accounts/login/' in response.url


def test_owner_profile_shows_edit_button(client):
    owner = create_owner()
    dog = Dog.objects.create(
        name='HomeDog',
        owner=owner,
        status=Dog.Status.RELEASED,
        registration_approval_status=Dog.RegistrationApprovalStatus.APPROVED,
    )
    client.force_login(owner)

    response = client.get(f'/dogs/my-dogs/{dog.id}/')

    assert response.status_code == 200
    assert f'/dogs/my-dogs/{dog.id}/edit/'.encode() in response.content


def test_owner_can_edit_owned_dog_profile(client):
    owner = create_owner()
    dog = Dog.objects.create(
        name='HomeDog',
        owner=owner,
        status=Dog.Status.RELEASED,
        vaccination_status=Dog.VaccinationStatus.UNVACCINATED,
        vaccination_request=True,
        registration_approval_status=Dog.RegistrationApprovalStatus.APPROVED,
    )
    client.force_login(owner)

    response = client.post(
        f'/dogs/my-dogs/{dog.id}/edit/',
        {
            'name': 'UpdatedName',
            'sex': 'male',
            'age_estimate': '2 years',
            'color': 'black',
            'barangay': 'Suba',
            'notes': 'updated notes',
            'vaccination_status': Dog.VaccinationStatus.UNVACCINATED,
            'vaccination_request': 'on',
        },
        follow=True,
    )

    assert response.status_code == 200
    dog.refresh_from_db()
    assert dog.name == 'UpdatedName'
    assert dog.barangay == 'Suba'
    assert dog.color == 'black'


def test_owner_cannot_edit_other_owner_dog_profile(client):
    owner = create_owner('owner@example.com')
    other = create_owner('other@example.com')
    dog = Dog.objects.create(
        name='HomeDog',
        owner=owner,
        status=Dog.Status.RELEASED,
        registration_approval_status=Dog.RegistrationApprovalStatus.APPROVED,
    )
    client.force_login(other)

    response = client.get(f'/dogs/my-dogs/{dog.id}/edit/')

    assert response.status_code == 404


def test_owner_can_request_new_schedule_when_vaccine_expired(client):
    owner = create_owner()
    User = get_user_model()
    staff = User.objects.create_user(
        username='staff@example.com',
        email='staff@example.com',
        password='StrongPass123!',
        role='STAFF',
        email_verified=True,
        is_verified=True,
        legal_consent=True,
    )
    dog = Dog.objects.create(
        name='ExpiredDog',
        owner=owner,
        status=Dog.Status.RELEASED,
        vaccination_status=Dog.VaccinationStatus.VACCINATED,
        vaccination_proof='vaccination_proofs/old-proof.pdf',
        registration_approval_status=Dog.RegistrationApprovalStatus.APPROVED,
    )
    VaccinationRecord.objects.create(
        dog=dog,
        vaccine_type='Anti-rabies',
        vaccinated_date=timezone.localdate() - timedelta(days=400),
        expiration_date=timezone.localdate() - timedelta(days=1),
    )
    client.force_login(owner)

    response = client.post(
        f'/dogs/my-dogs/{dog.id}/request-vaccination/',
        follow=True,
    )

    dog.refresh_from_db()
    assert response.status_code == 200
    assert dog.vaccination_status == Dog.VaccinationStatus.UNVACCINATED
    assert dog.vaccination_request is True
    assert dog.vaccination_proof.name == ''
    assert Notification.objects.filter(user=staff, title='New vaccination schedule request').exists()


def test_owner_cannot_request_new_schedule_before_expiry(client):
    owner = create_owner()
    dog = Dog.objects.create(
        name='ActiveDog',
        owner=owner,
        status=Dog.Status.RELEASED,
        vaccination_status=Dog.VaccinationStatus.VACCINATED,
        registration_approval_status=Dog.RegistrationApprovalStatus.APPROVED,
    )
    VaccinationRecord.objects.create(
        dog=dog,
        vaccine_type='Anti-rabies',
        vaccinated_date=timezone.localdate() - timedelta(days=5),
        expiration_date=timezone.localdate() + timedelta(days=30),
    )
    client.force_login(owner)

    response = client.post(
        f'/dogs/my-dogs/{dog.id}/request-vaccination/',
        follow=True,
    )

    dog.refresh_from_db()
    assert response.status_code == 200
    assert dog.vaccination_status == Dog.VaccinationStatus.VACCINATED
    assert dog.vaccination_request is False


def test_unverified_owner_redirected_from_new_schedule_request(client):
    owner = create_owner(verified=False)
    dog = Dog.objects.create(
        name='NeedRenewal',
        owner=owner,
        status=Dog.Status.RELEASED,
        vaccination_status=Dog.VaccinationStatus.VACCINATED,
    )
    VaccinationRecord.objects.create(
        dog=dog,
        vaccine_type='Anti-rabies',
        vaccinated_date=timezone.localdate() - timedelta(days=365),
        expiration_date=timezone.localdate() - timedelta(days=1),
    )
    client.force_login(owner)

    response = client.post(f'/dogs/my-dogs/{dog.id}/request-vaccination/')

    assert response.status_code == 302
    assert '/accounts/verification/' in response.url


def test_unverified_owner_redirected_from_edit_dog_profile(client):
    owner = create_owner(verified=False)
    dog = Dog.objects.create(
        name='HomeDog',
        owner=owner,
        status=Dog.Status.RELEASED,
        vaccination_status=Dog.VaccinationStatus.UNVACCINATED,
        vaccination_request=True,
    )
    client.force_login(owner)

    response = client.get(f'/dogs/my-dogs/{dog.id}/edit/')

    assert response.status_code == 302
    assert '/accounts/verification/' in response.url
