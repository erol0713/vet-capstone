from django.contrib.auth import get_user_model
from django.utils import timezone

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


def test_staff_list_orders_unresolved_before_completed(client):
    staff = create_staff()
    client.force_login(staff)
    now = timezone.now()

    open_report = Report.objects.create(
        report_type='STRAY',
        location='Poblacion',
        status=Report.Status.OPEN,
    )
    in_review_report = Report.objects.create(
        report_type='STRAY',
        location='Poblacion',
        status=Report.Status.IN_REVIEW,
    )
    resolved_report = Report.objects.create(
        report_type='STRAY',
        location='Poblacion',
        status=Report.Status.RESOLVED,
    )
    closed_report = Report.objects.create(
        report_type='STRAY',
        location='Poblacion',
        status=Report.Status.CLOSED,
    )

    Report.objects.filter(id=open_report.id).update(created_at=now - timezone.timedelta(days=2))
    Report.objects.filter(id=in_review_report.id).update(created_at=now - timezone.timedelta(days=1))
    Report.objects.filter(id=resolved_report.id).update(created_at=now)
    Report.objects.filter(id=closed_report.id).update(created_at=now - timezone.timedelta(days=3))

    response = client.get('/staff/reports/')

    assert response.status_code == 200
    ordered = list(response.context['reports'])
    assert ordered[0].id == in_review_report.id
    assert ordered[1].id == open_report.id
    assert ordered[-2].id == resolved_report.id
    assert ordered[-1].id == closed_report.id
