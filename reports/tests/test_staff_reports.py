from django.contrib.auth import get_user_model

from notifications.models import Notification
from reports.models import Report


def create_staff():
    User = get_user_model()
    return User.objects.create_user(
        username='staff@reports.test',
        email='staff@reports.test',
        password='StrongPass123!',
        role='STAFF',
        email_verified=True,
        is_verified=True,
        legal_consent=True,
    )


def create_user():
    User = get_user_model()
    return User.objects.create_user(
        username='user@reports.test',
        email='user@reports.test',
        password='StrongPass123!',
        role='OWNER',
        email_verified=True,
        is_verified=True,
        legal_consent=True,
    )


def test_staff_can_update_status_and_notify(client):
    staff = create_staff()
    user = create_user()
    report = Report.objects.create(
        report_type='STRAY',
        reported_by=user,
        location='Poblacion',
    )
    client.force_login(staff)

    response = client.post(
        f'/staff/reports/{report.id}/status/',
        {'status': 'IN_REVIEW', 'notes': 'Checking'},
        follow=True,
    )

    report.refresh_from_db()
    assert response.status_code == 200
    assert report.status == 'IN_REVIEW'
    assert Notification.objects.filter(user=user).exists()
