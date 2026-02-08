import pytest
from django.urls import reverse

from reports.models import Report
from users.models import CustomUser


@pytest.mark.django_db
def test_public_delete_requires_login(client):
    report = Report.objects.create(report_type='STRAY', location='Test location')
    response = client.post(reverse('reports_public_delete', args=[report.id]))
    assert response.status_code == 302
    assert Report.objects.filter(id=report.id).exists()


@pytest.mark.django_db
def test_public_delete_owner_success(client):
    user = CustomUser.objects.create_user(
        username='owner',
        email='owner@example.com',
        password='testpass123',
        role=CustomUser.Roles.OWNER,
        email_verified=True,
        is_verified=True,
    )
    report = Report.objects.create(report_type='STRAY', location='Test location', reported_by=user)
    client.login(username='owner', password='testpass123')
    response = client.post(reverse('reports_public_delete', args=[report.id]))
    assert response.status_code == 302
    assert not Report.objects.filter(id=report.id).exists()


@pytest.mark.django_db
def test_public_delete_non_owner_denied(client):
    owner = CustomUser.objects.create_user(
        username='owner2',
        email='owner2@example.com',
        password='testpass123',
        role=CustomUser.Roles.OWNER,
        email_verified=True,
        is_verified=True,
    )
    other = CustomUser.objects.create_user(
        username='other',
        email='other@example.com',
        password='testpass123',
        role=CustomUser.Roles.OWNER,
        email_verified=True,
        is_verified=True,
    )
    report = Report.objects.create(report_type='STRAY', location='Test location', reported_by=owner)
    client.login(username='other', password='testpass123')
    response = client.post(reverse('reports_public_delete', args=[report.id]))
    assert response.status_code == 302
    assert Report.objects.filter(id=report.id).exists()
