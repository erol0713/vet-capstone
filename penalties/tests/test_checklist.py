from django.contrib.auth import get_user_model


def create_staff():
    User = get_user_model()
    return User.objects.create_user(
        username='staff@penalty.test',
        email='staff@penalty.test',
        password='StrongPass123!',
        role='STAFF',
        email_verified=True,
        is_verified=True,
        legal_consent=True,
    )


def test_checklist_requires_staff(client):
    response = client.get('/staff/penalties/checklist/', follow=True)

    assert response.status_code == 200
    assert b'login' in response.content.lower()


def test_staff_can_view_checklist(client):
    staff = create_staff()
    client.force_login(staff)

    response = client.get('/staff/penalties/checklist/')

    assert response.status_code == 200
    assert b'Penalty Checklist' in response.content
