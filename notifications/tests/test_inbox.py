from django.contrib.auth import get_user_model
from django.urls import reverse

from notifications.models import Notification


def create_user():
    User = get_user_model()
    return User.objects.create_user(
        username='notify@example.com',
        email='notify@example.com',
        password='StrongPass123!',
        role='OWNER',
        email_verified=True,
        is_verified=True,
        legal_consent=True,
    )


def test_inbox_requires_login(client):
    response = client.get('/notifications/', follow=True)
    assert response.status_code == 200
    assert b'login' in response.content.lower()


def test_unread_count_in_context(client):
    user = create_user()
    Notification.objects.create(user=user, title='Alert', message='Test')
    client.force_login(user)

    response = client.get('/notifications/')

    assert response.status_code == 200
    assert b'Notifications' in response.content


def test_navbar_notification_bell_dropdown(client):
    user = create_user()
    Notification.objects.create(user=user, title='Bell Test', message='Navbar dropdown item')
    client.force_login(user)

    response = client.get('/notifications/')

    assert response.status_code == 200
    assert b'bi-bell' in response.content
    assert b'notificationsMenu' in response.content
    assert b'Bell Test' in response.content


def test_mark_read(client):
    user = create_user()
    notification = Notification.objects.create(user=user, title='Alert', message='Test')
    client.force_login(user)

    response = client.get(f'/notifications/read/{notification.id}/', follow=True)

    notification.refresh_from_db()
    assert response.status_code == 200
    assert notification.is_read is True


def test_mark_read_redirects_to_action_url(client):
    user = create_user()
    action_url = reverse('reports_public_list')
    notification = Notification.objects.create(
        user=user,
        title='Alert',
        message='Test',
        action_url=action_url,
    )
    client.force_login(user)

    response = client.get(f'/notifications/read/{notification.id}/')

    notification.refresh_from_db()
    assert response.status_code == 302
    assert response.url == action_url
    assert notification.is_read is True


def test_mark_read_blocks_external_action_url(client):
    user = create_user()
    notification = Notification.objects.create(
        user=user,
        title='Alert',
        message='Test',
        action_url='https://example.com/phishing',
    )
    client.force_login(user)

    response = client.get(f'/notifications/read/{notification.id}/')

    notification.refresh_from_db()
    assert response.status_code == 302
    assert response.url == reverse('notifications_inbox')
    assert notification.is_read is True
