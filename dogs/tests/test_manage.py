from django.contrib.auth import get_user_model
from django.utils import timezone

from notifications.models import Notification
from dogs.models import Dog
from vaccinations.models import VaccinationRecord


def create_user(role):
    User = get_user_model()
    return User.objects.create_user(
        username=f'{role.lower()}@example.com',
        email=f'{role.lower()}@example.com',
        password='StrongPass123!',
        role=role,
        email_verified=True,
        is_verified=True,
        legal_consent=True,
    )


def test_staff_can_access_manage_list(client):
    staff = create_user('STAFF')
    client.force_login(staff)

    response = client.get('/staff/dogs/')

    assert response.status_code == 200


def test_staff_can_access_registered_by_owner(client):
    staff = create_user('STAFF')
    client.force_login(staff)

    response = client.get('/staff/dogs/registered/')

    assert response.status_code == 200


def test_staff_can_view_registered_detail(client):
    staff = create_user('STAFF')
    owner = create_user('OWNER')
    dog = Dog.objects.create(
        name='OwnedDog',
        status=Dog.Status.RELEASED,
        owner=owner,
    )
    client.force_login(staff)

    response = client.get(f'/staff/dogs/registered/{dog.id}/')

    assert response.status_code == 200
    assert b'OwnedDog' in response.content


def test_staff_can_access_vaccination_requests(client):
    staff = create_user('STAFF')
    client.force_login(staff)

    response = client.get('/staff/dogs/vaccinations/')

    assert response.status_code == 200


def test_owner_blocked_from_manage_list(client):
    owner = create_user('OWNER')
    client.force_login(owner)

    response = client.get('/staff/dogs/', follow=True)

    assert response.status_code == 200
    assert b'permission' in response.content.lower()


def test_owner_blocked_from_registered_by_owner(client):
    owner = create_user('OWNER')
    client.force_login(owner)

    response = client.get('/staff/dogs/registered/', follow=True)

    assert response.status_code == 200
    assert b'permission' in response.content.lower()


def test_owner_blocked_from_registered_detail(client):
    owner = create_user('OWNER')
    dog = Dog.objects.create(
        name='OwnedDog',
        status=Dog.Status.RELEASED,
        owner=owner,
    )
    client.force_login(owner)

    response = client.get(f'/staff/dogs/registered/{dog.id}/', follow=True)

    assert response.status_code == 200
    assert b'permission' in response.content.lower()


def test_owner_blocked_from_vaccination_requests(client):
    owner = create_user('OWNER')
    client.force_login(owner)

    response = client.get('/staff/dogs/vaccinations/', follow=True)

    assert response.status_code == 200
    assert b'permission' in response.content.lower()


def test_staff_can_create_dog(client):
    staff = create_user('STAFF')
    client.force_login(staff)

    response = client.post(
        '/staff/dogs/new/',
        {
            'name': 'Scout',
            'status': 'AVAILABLE',
            'barangay': 'Poblacion',
        },
        follow=True,
    )

    assert response.status_code == 200
    assert Dog.objects.filter(name='Scout').exists()


def test_staff_can_delete_dog(client):
    staff = create_user('STAFF')
    dog = Dog.objects.create(name='DeleteMe', status=Dog.Status.IMPOUNDED)
    client.force_login(staff)

    response = client.post(f'/staff/dogs/{dog.id}/delete/', follow=True)

    assert response.status_code == 200
    assert not Dog.objects.filter(id=dog.id).exists()


def test_intake_with_capture_datetime_forces_impounded_status(client):
    staff = create_user('STAFF')
    client.force_login(staff)

    response = client.post(
        '/staff/dogs/new/',
        {
            'name': 'Captured',
            'status': 'AVAILABLE',
            'capture_datetime': '2026-01-30T10:00',
            'barangay': 'Poblacion',
        },
        follow=True,
    )

    dog = Dog.objects.get(name='Captured')
    assert response.status_code == 200
    assert dog.status == Dog.Status.IMPOUNDED


def test_intake_without_surrender_sets_impounded(client):
    staff = create_user('STAFF')
    client.force_login(staff)

    response = client.post(
        '/staff/dogs/new/',
        {
            'name': 'NoDates',
            'status': 'AVAILABLE',
            'barangay': 'Poblacion',
        },
        follow=True,
    )

    dog = Dog.objects.get(name='NoDates')
    assert response.status_code == 200
    assert dog.status == Dog.Status.IMPOUNDED


def test_intake_with_capture_and_owner_shows_validation_error(client):
    staff = create_user('STAFF')
    owner = create_user('OWNER')
    client.force_login(staff)

    response = client.post(
        '/staff/dogs/new/',
        {
            'name': 'InvalidCaptured',
            'status': 'AVAILABLE',
            'owner': owner.id,
            'capture_datetime': '2026-01-30T10:00',
            'barangay': 'Poblacion',
        },
        follow=True,
    )

    assert response.status_code == 200
    assert b'Unable to create intake record.' in response.content
    assert b'Captured dogs should not have an owner.' in response.content
    assert not Dog.objects.filter(name='InvalidCaptured').exists()


def test_intake_with_surrender_sets_available(client):
    staff = create_user('STAFF')
    client.force_login(staff)

    response = client.post(
        '/staff/dogs/new/',
        {
            'name': 'Surrendered',
            'status': 'AVAILABLE',
            'surrender_datetime': '2026-01-30T10:00',
            'barangay': 'Poblacion',
        },
        follow=True,
    )

    dog = Dog.objects.get(name='Surrendered')
    assert response.status_code == 200
    assert dog.status == Dog.Status.AVAILABLE


def test_edit_intake_enforces_status(client):
    staff = create_user('STAFF')
    dog = Dog.objects.create(name='EditMe', status=Dog.Status.ADOPTED)
    client.force_login(staff)

    response = client.post(
        f'/staff/dogs/{dog.id}/edit/',
        {
            'name': 'EditMe',
            'status': 'AVAILABLE',
            'capture_datetime': '2026-01-30T10:00',
            'barangay': 'Poblacion',
        },
        follow=True,
    )

    dog.refresh_from_db()
    assert response.status_code == 200
    assert dog.status == Dog.Status.IMPOUNDED


def test_edit_registered_dog_rejects_disallowed_status(client):
    staff = create_user('STAFF')
    owner = create_user('OWNER')
    dog = Dog.objects.create(
        name='Registered',
        status=Dog.Status.RELEASED,
        owner=owner,
    )
    client.force_login(staff)

    response = client.post(
        f'/staff/dogs/{dog.id}/edit/',
        {
            'name': 'Registered',
            'status': 'RELEASED',
            'owner': owner.id,
            'barangay': 'Poblacion',
        },
        follow=True,
    )

    dog.refresh_from_db()
    assert response.status_code == 200
    assert dog.status == Dog.Status.RELEASED
    assert 'status' in response.context['form'].errors


def test_staff_setting_vaccination_schedule_notifies_owner(client):
    staff = create_user('STAFF')
    owner = create_user('OWNER')
    dog = Dog.objects.create(
        name='VaccDog',
        status=Dog.Status.RELEASED,
        owner=owner,
        vaccination_status=Dog.VaccinationStatus.UNVACCINATED,
        vaccination_request=True,
    )
    client.force_login(staff)

    response = client.post(
        f'/staff/dogs/{dog.id}/schedule/',
        {'appointment_date': '2026-02-04', 'appointment_time': '09:00'},
        follow=True,
    )

    assert response.status_code == 200
    assert Notification.objects.filter(user=owner, title__icontains='Vaccination').exists()


def test_staff_can_record_vaccination_dates(client):
    staff = create_user('STAFF')
    owner = create_user('OWNER')
    dog = Dog.objects.create(
        name='ClinicDog',
        status=Dog.Status.RELEASED,
        owner=owner,
        vaccination_status=Dog.VaccinationStatus.UNVACCINATED,
        vaccination_request=True,
        vaccination_schedule=timezone.now(),
    )
    client.force_login(staff)

    response = client.post(
        f'/staff/dogs/{dog.id}/vaccination-record/',
        {
            'vaccine_type': 'Anti-rabies',
            'vaccinated_date': '2026-02-20',
            'expiration_date': '2027-02-20',
        },
        follow=True,
    )

    dog.refresh_from_db()
    record = VaccinationRecord.objects.get(dog=dog)
    assert response.status_code == 200
    assert record.vaccinated_date.isoformat() == '2026-02-20'
    assert record.expiration_date.isoformat() == '2027-02-20'
    assert dog.vaccination_status == Dog.VaccinationStatus.VACCINATED
    assert dog.vaccination_request is False
    assert dog.vaccination_schedule is None
    assert dog.registration_approval_status == Dog.RegistrationApprovalStatus.APPROVED
    assert Notification.objects.filter(user=owner, title='Vaccination Recorded').exists()


def test_staff_can_record_vaccination_with_owner_proof_expiration_only(client):
    staff = create_user('STAFF')
    owner = create_user('OWNER')
    dog = Dog.objects.create(
        name='ProofDog',
        status=Dog.Status.RELEASED,
        owner=owner,
        vaccination_status=Dog.VaccinationStatus.UNVACCINATED,
        vaccination_request=True,
    )
    client.force_login(staff)

    response = client.post(
        f'/staff/dogs/{dog.id}/vaccination-record/',
        {
            'vaccine_type': 'General Vaccine',
            'expiration_date': '2026-12-30',
            'from_owner_proof': 'on',
        },
        follow=True,
    )

    dog.refresh_from_db()
    record = VaccinationRecord.objects.get(dog=dog)
    assert response.status_code == 200
    assert record.vaccinated_date is None
    assert record.from_owner_proof is True
    assert record.expiration_date.isoformat() == '2026-12-30'
    assert dog.vaccination_status == Dog.VaccinationStatus.VACCINATED
    assert dog.registration_approval_status == Dog.RegistrationApprovalStatus.APPROVED


def test_record_vaccination_requires_vaccinated_date_without_proof_flag(client):
    staff = create_user('STAFF')
    owner = create_user('OWNER')
    dog = Dog.objects.create(
        name='NeedsDate',
        status=Dog.Status.RELEASED,
        owner=owner,
        vaccination_status=Dog.VaccinationStatus.UNVACCINATED,
        vaccination_request=True,
    )
    client.force_login(staff)

    response = client.post(
        f'/staff/dogs/{dog.id}/vaccination-record/',
        {
            'vaccine_type': 'General Vaccine',
            'expiration_date': '2027-01-01',
        },
    )

    assert response.status_code == 200
    assert not VaccinationRecord.objects.filter(dog=dog).exists()


def test_owner_blocked_from_record_vaccination_page(client):
    owner = create_user('OWNER')
    dog = Dog.objects.create(
        name='OwnedDog',
        status=Dog.Status.RELEASED,
        owner=owner,
    )
    client.force_login(owner)

    response = client.get(f'/staff/dogs/{dog.id}/vaccination-record/', follow=True)

    assert response.status_code == 200
    assert b'permission' in response.content.lower()


def test_staff_cannot_approve_registration_without_vaccination_evidence(client):
    staff = create_user('STAFF')
    owner = create_user('OWNER')
    dog = Dog.objects.create(
        name='NoEvidence',
        status=Dog.Status.RELEASED,
        owner=owner,
        vaccination_status=Dog.VaccinationStatus.UNVACCINATED,
        vaccination_request=True,
        registration_approval_status=Dog.RegistrationApprovalStatus.PENDING,
    )
    client.force_login(staff)

    response = client.post(
        f'/staff/dogs/registered/{dog.id}/',
        {'action': 'approve'},
        follow=True,
    )

    dog.refresh_from_db()
    assert response.status_code == 200
    assert dog.registration_approval_status == Dog.RegistrationApprovalStatus.PENDING
