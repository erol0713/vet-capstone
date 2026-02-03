from decimal import Decimal

from django.contrib.auth import get_user_model

from dogs.models import Dog
from penalties.models import PenaltyCase, PenaltyChecklistItem, PenaltyLineItem


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


def test_save_checklist_creates_line_items(client):
    staff = create_staff()
    dog = Dog.objects.create()
    case = PenaltyCase.objects.create(dog=dog, owner=staff)
    item = PenaltyChecklistItem.objects.create(
        code='S28-001',
        section='SECTION_28',
        description='First offense stray dog',
        default_amount=Decimal('500.00'),
    )
    client.force_login(staff)

    response = client.post(
        f'/staff/penalties/checklist/?case={case.id}',
        {
            'action': 'save',
            'case_id': case.id,
            'items': [item.code],
        },
        follow=True,
    )

    assert response.status_code == 200
    assert PenaltyLineItem.objects.filter(case=case).count() == 1


def test_finalize_locks_case(client):
    staff = create_staff()
    dog = Dog.objects.create()
    case = PenaltyCase.objects.create(dog=dog, owner=staff)
    client.force_login(staff)

    response = client.post(
        f'/staff/penalties/checklist/?case={case.id}',
        {'action': 'finalize', 'case_id': case.id},
        follow=True,
    )

    case.refresh_from_db()
    assert response.status_code == 200
    assert case.is_finalized is True


def test_cannot_save_after_finalize(client):
    staff = create_staff()
    dog = Dog.objects.create()
    case = PenaltyCase.objects.create(dog=dog, owner=staff, is_finalized=True)
    item = PenaltyChecklistItem.objects.create(
        code='S29-001',
        section='SECTION_29',
        description='Unregistered dog',
        default_amount=Decimal('200.00'),
    )
    client.force_login(staff)

    response = client.post(
        f'/staff/penalties/checklist/?case={case.id}',
        {
            'action': 'save',
            'case_id': case.id,
            'items': [item.code],
        },
        follow=True,
    )

    assert response.status_code == 200
    assert PenaltyLineItem.objects.filter(case=case).count() == 0


def test_lodging_and_redemption_not_added_to_total(client):
    staff = create_staff()
    dog = Dog.objects.create()
    case = PenaltyCase.objects.create(dog=dog, owner=staff)
    item = PenaltyChecklistItem.objects.create(
        code='S28-002',
        section='SECTION_28',
        description='Impound fee',
        default_amount=Decimal('500.00'),
    )
    client.force_login(staff)

    response = client.post(
        f'/staff/penalties/checklist/?case={case.id}',
        {
            'action': 'save',
            'case_id': case.id,
            'items': [item.code],
            'redemption_fee': '200',
            'lodging_days': '2',
            'lodging_rate': '200',
        },
        follow=True,
    )

    case.refresh_from_db()
    assert response.status_code == 200
    assert case.total_amount == Decimal('500.00')
    assert PenaltyLineItem.objects.filter(case=case).count() == 1


def test_checklist_totals_only_selected_items(client):
    staff = create_staff()
    dog = Dog.objects.create()
    case = PenaltyCase.objects.create(dog=dog, owner=staff)
    item = PenaltyChecklistItem.objects.create(
        code='S29-009',
        section='SECTION_29',
        description='No leash',
        default_amount=Decimal('500.00'),
    )
    client.force_login(staff)

    response = client.post(
        f'/staff/penalties/checklist/?case={case.id}',
        {
            'action': 'save',
            'case_id': case.id,
            'items': [item.code],
        },
        follow=True,
    )

    case.refresh_from_db()
    assert response.status_code == 200
    assert case.total_amount == Decimal('500.00')
