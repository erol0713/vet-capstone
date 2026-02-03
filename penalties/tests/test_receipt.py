from decimal import Decimal

from django.contrib.auth import get_user_model

from dogs.models import Dog
from penalties.models import PenaltyCase, PenaltyLineItem


def create_staff():
    User = get_user_model()
    return User.objects.create_user(
        username='staff@receipt.test',
        email='staff@receipt.test',
        password='StrongPass123!',
        role='STAFF',
        email_verified=True,
        is_verified=True,
        legal_consent=True,
    )


def test_receipt_requires_staff(client):
    response = client.get('/staff/penalties/receipt/1/', follow=True)

    assert response.status_code == 200
    assert b'login' in response.content.lower()


def test_staff_can_view_receipt(client):
    staff = create_staff()
    dog = Dog.objects.create(name='Buddy')
    case = PenaltyCase.objects.create(dog=dog, owner=staff, total_amount=Decimal('500.00'))
    PenaltyLineItem.objects.create(
        case=case,
        description='Sec 29.9: No dog leash in public',
        quantity=1,
        unit_amount=Decimal('500.00'),
        total=Decimal('500.00'),
    )
    client.force_login(staff)

    response = client.get(f'/staff/penalties/receipt/{case.id}/')

    assert response.status_code == 200
    assert b'CITATION TICKET' in response.content
    assert staff.email.encode() in response.content


def test_receipt_404_for_missing_case(client):
    staff = create_staff()
    client.force_login(staff)

    response = client.get('/staff/penalties/receipt/99999/')

    assert response.status_code == 404
