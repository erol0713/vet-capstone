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


def test_dashboard_renders_date_range_and_chart_data(client):
    staff = create_staff()
    client.force_login(staff)

    response = client.get('/staff/analytics/?start=2026-01-01&end=2026-01-31')

    assert response.status_code == 200
    assert b'analytics-chart-data' in response.content
    assert b'value=\"2026-01-01\"' in response.content
    assert b'value=\"2026-01-31\"' in response.content
