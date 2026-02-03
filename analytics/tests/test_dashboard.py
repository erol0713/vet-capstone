from django.contrib.auth import get_user_model


def create_staff():
    User = get_user_model()
    return User.objects.create_user(
        username='analytics@example.com',
        email='analytics@example.com',
        password='StrongPass123!',
        role='STAFF',
        email_verified=True,
        is_verified=True,
        legal_consent=True,
    )


def test_dashboard_requires_login(client):
    response = client.get('/staff/analytics/', follow=True)
    assert response.status_code == 200
    assert b'login' in response.content.lower()


def test_staff_can_view_dashboard(client):
    staff = create_staff()
    client.force_login(staff)

    response = client.get('/staff/analytics/')

    assert response.status_code == 200
    assert b'Analytics Dashboard' in response.content
