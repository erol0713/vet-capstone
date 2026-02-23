from django.utils import timezone

from adoption.models import AdoptionReservation, ReclaimRequest
from dogs.models import Dog
from reports.models import Report
from users.models import CustomUser


def create_user(**overrides):
    defaults = {
        'username': 'owner@example.com',
        'email': 'owner@example.com',
        'password': 'StrongPass123!',
        'legal_consent': True,
        'legal_consented_at': timezone.now(),
    }
    defaults.update(overrides)
    return CustomUser.objects.create_user(**defaults)


def create_dog(**overrides):
    defaults = {
        'name': 'Buddy',
        'color': 'Brown',
        'sex': 'Male',
    }
    defaults.update(overrides)
    return Dog.objects.create(**defaults)


def test_dashboard_counts_include_reports_adoption_reclaim(client):
    user = create_user()
    dog = create_dog()
    Report.objects.create(report_type='STRAY', location='Test', reported_by=user)
    AdoptionReservation.objects.create(dog=dog, requester=user)
    ReclaimRequest.objects.create(dog=dog, owner=user)

    client.force_login(user)
    response = client.get('/accounts/dashboard/')

    assert response.status_code == 200
    assert response.context['report_count'] == 1
    assert response.context['adoption_count'] == 1
    assert response.context['reclaim_count'] == 1
