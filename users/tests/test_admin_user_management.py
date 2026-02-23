from django.utils import timezone

from users.models import CustomUser, FaceVerification


def create_user(**overrides):
    defaults = {
        'username': 'user@example.com',
        'email': 'user@example.com',
        'password': 'StrongPass123!',
        'legal_consent': True,
        'legal_consented_at': timezone.now(),
    }
    defaults.update(overrides)
    return CustomUser.objects.create_user(**defaults)


def test_admin_user_management_access(client):
    admin_user = create_user(
        username='admin@example.com',
        email='admin@example.com',
        role=CustomUser.Roles.ADMIN,
    )
    client.force_login(admin_user)

    response = client.get('/accounts/admin/users/')

    assert response.status_code == 200


def test_staff_cannot_access_admin_user_management(client):
    staff_user = create_user(
        username='staff@example.com',
        email='staff@example.com',
        role=CustomUser.Roles.STAFF,
    )
    client.force_login(staff_user)

    response = client.get('/accounts/admin/users/')

    assert response.status_code == 302


def test_admin_can_approve_face_verification(client):
    admin_user = create_user(
        username='admin2@example.com',
        email='admin2@example.com',
        role=CustomUser.Roles.ADMIN,
    )
    target_user = create_user(
        username='target@example.com',
        email='target@example.com',
        role=CustomUser.Roles.OWNER,
        is_verified=False,
    )
    FaceVerification.objects.create(user=target_user, status=FaceVerification.Status.PENDING)

    client.force_login(admin_user)
    response = client.post(
        '/accounts/admin/users/action/',
        {'action': 'approve_face', 'user_id': target_user.id},
    )

    assert response.status_code == 302
    target_user.refresh_from_db()
    record = FaceVerification.objects.get(user=target_user)
    assert record.status == FaceVerification.Status.APPROVED
    assert record.reviewed_by == admin_user
    assert target_user.is_verified is True


def test_admin_can_reject_face_verification(client):
    admin_user = create_user(
        username='admin3@example.com',
        email='admin3@example.com',
        role=CustomUser.Roles.ADMIN,
    )
    target_user = create_user(
        username='reject@example.com',
        email='reject@example.com',
        role=CustomUser.Roles.OWNER,
        is_verified=True,
    )
    FaceVerification.objects.create(user=target_user, status=FaceVerification.Status.PENDING)

    client.force_login(admin_user)
    response = client.post(
        '/accounts/admin/users/action/',
        {'action': 'reject_face', 'user_id': target_user.id},
    )

    assert response.status_code == 302
    target_user.refresh_from_db()
    record = FaceVerification.objects.get(user=target_user)
    assert record.status == FaceVerification.Status.REJECTED
    assert target_user.is_verified is False


def test_admin_can_toggle_email_verification(client):
    admin_user = create_user(
        username='admin4@example.com',
        email='admin4@example.com',
        role=CustomUser.Roles.ADMIN,
    )
    target_user = create_user(
        username='email@example.com',
        email='email@example.com',
        email_verified=False,
    )
    client.force_login(admin_user)

    response = client.post(
        '/accounts/admin/users/action/',
        {'action': 'mark_email_verified', 'user_id': target_user.id},
    )

    assert response.status_code == 302
    target_user.refresh_from_db()
    assert target_user.email_verified is True
