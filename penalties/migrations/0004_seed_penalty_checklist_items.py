from decimal import Decimal

from django.db import migrations


def seed_penalty_items(apps, schema_editor):
    PenaltyChecklistItem = apps.get_model('penalties', 'PenaltyChecklistItem')
    items = [
        {
            'code': 'S28_1_RABIES_FEE',
            'section': 'SECTION_28',
            'description': 'Sec 28.1: Rabies vaccination service fee',
            'default_amount': Decimal('50.00'),
        },
        {
            'code': 'S28_2_LODGING_DAILY',
            'section': 'SECTION_28',
            'description': 'Sec 28.2: Lodging fee (Daily)',
            'default_amount': Decimal('200.00'),
        },
        {
            'code': 'S28_3_IMPOUND_FEE',
            'section': 'SECTION_28',
            'description': 'Sec 28.3: Impoundment fee',
            'default_amount': Decimal('500.00'),
        },
        {
            'code': 'S28_4_LOST_CERT',
            'section': 'SECTION_28',
            'description': 'Sec 28.4: Lost vaccination certificate',
            'default_amount': Decimal('100.00'),
        },
        {
            'code': 'S28_5_NEUTER_MALE',
            'section': 'SECTION_28',
            'description': 'Sec 28.5: Neutering (Male)',
            'default_amount': Decimal('4000.00'),
        },
        {
            'code': 'S28_5_NEUTER_FEMALE',
            'section': 'SECTION_28',
            'description': 'Sec 28.5: Neutering (Female)',
            'default_amount': Decimal('5000.00'),
        },
        {
            'code': 'S28_6_VET_CLEARANCE',
            'section': 'SECTION_28',
            'description': 'Sec 28.6: Veterinary clearance',
            'default_amount': Decimal('100.00'),
        },
        {
            'code': 'S29_1_DOG_SLAUGHTER',
            'section': 'SECTION_29',
            'description': 'Sec 29.1: Dog slaughter / Meat trade',
            'default_amount': Decimal('5000.00'),
        },
        {
            'code': 'S29_2_NO_VAX_PROOF',
            'section': 'SECTION_29',
            'description': 'Sec 29.2: No proof of vaccination',
            'default_amount': Decimal('2000.00'),
        },
        {
            'code': 'S29_3_REFUSE_REGISTER',
            'section': 'SECTION_29',
            'description': 'Sec 29.3: Refusal to register/vaccinate',
            'default_amount': Decimal('2000.00'),
        },
        {
            'code': 'S29_4_UNVAX_BITE',
            'section': 'SECTION_29',
            'description': 'Sec 29.4: Unvaccinated dog bit a victim',
            'default_amount': Decimal('5000.00'),
        },
        {
            'code': 'S29_9_NO_LEASH',
            'section': 'SECTION_29',
            'description': 'Sec 29.9: No dog leash in public',
            'default_amount': Decimal('500.00'),
        },
        {
            'code': 'S29_11_CAPTURED_NO_TAG',
            'section': 'SECTION_29',
            'description': 'Sec 29.11: Captured dog without tag',
            'default_amount': Decimal('3000.00'),
        },
        {
            'code': 'S29_12_LOST_VAX_CARD',
            'section': 'SECTION_29',
            'description': 'Sec 29.12: Lost vaccination card',
            'default_amount': Decimal('500.00'),
        },
        {
            'code': 'S29_16_CRUELTY',
            'section': 'SECTION_29',
            'description': 'Sec 29.16: Cruelty to dog',
            'default_amount': Decimal('5000.00'),
        },
        {
            'code': 'S29_22_NO_POOP_CLEAN',
            'section': 'SECTION_29',
            'description': 'Sec 29.22: Failure to clean poop in public',
            'default_amount': Decimal('500.00'),
        },
        {
            'code': 'S29_24_EXCESS_1',
            'section': 'SECTION_29',
            'description': 'Sec 29.24: Exceeding 4 heads (1 excess)',
            'default_amount': Decimal('500.00'),
        },
        {
            'code': 'S29_24_EXCESS_2',
            'section': 'SECTION_29',
            'description': 'Sec 29.24: Exceeding 4 heads (2 excess)',
            'default_amount': Decimal('1000.00'),
        },
    ]

    for item in items:
        PenaltyChecklistItem.objects.get_or_create(code=item['code'], defaults=item)


class Migration(migrations.Migration):
    dependencies = [
        ('penalties', '0003_penaltychecklistitem_penaltycase_locked_by_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_penalty_items, migrations.RunPython.noop),
    ]
