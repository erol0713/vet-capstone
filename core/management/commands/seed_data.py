import random
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from adoption.models import AdoptionReservation, ReclaimRequest
from dogs.models import Dog
from notifications.models import Notification
from penalties.models import PenaltyCase, PenaltyChecklistItem, PenaltyLineItem
from reports.models import Report
from users.models import CustomUser
from vaccinations.models import VaccinationRecord


class Command(BaseCommand):
    help = "Seed demo data for local development."

    def add_arguments(self, parser):
        parser.add_argument("--seed", type=int, default=42, help="Random seed.")
        parser.add_argument("--owners", type=int, default=6, help="Number of owner users.")
        parser.add_argument("--dogs", type=int, default=10, help="Number of dogs.")
        parser.add_argument("--reports", type=int, default=8, help="Number of reports.")
        parser.add_argument("--adoptions", type=int, default=5, help="Number of adoption requests.")
        parser.add_argument("--reclaims", type=int, default=3, help="Number of reclaim requests.")
        parser.add_argument("--vaccinations", type=int, default=6, help="Number of vaccination records.")
        parser.add_argument("--penalties", type=int, default=3, help="Number of penalty cases.")
        parser.add_argument("--notifications", type=int, default=8, help="Number of notifications.")
        parser.add_argument(
            "--password",
            type=str,
            default="DemoPass123!",
            help="Password for all created users.",
        )

    def handle(self, *args, **options):
        random.seed(options["seed"])
        password = options["password"]

        with transaction.atomic():
            admin = self._get_or_create_admin(password)
            staff = self._get_or_create_staff(password)
            owners = self._get_or_create_owners(options["owners"], password)
            dogs = self._create_dogs(options["dogs"], owners)
            reports = self._create_reports(options["reports"], owners)
            adoptions = self._create_adoptions(options["adoptions"], owners, dogs)
            reclaims = self._create_reclaims(options["reclaims"], dogs)
            vaccinations = self._create_vaccinations(options["vaccinations"], dogs)
            penalties = self._create_penalties(options["penalties"], dogs)
            notifications = self._create_notifications(options["notifications"], owners, admin, staff)

        self.stdout.write(self.style.SUCCESS("Seed data created."))
        self.stdout.write(
            "Users: admin=%s staff=%s owners=%s | dogs=%s reports=%s adoptions=%s "
            "reclaims=%s vaccinations=%s penalties=%s notifications=%s"
            % (
                admin.email,
                staff.email,
                len(owners),
                len(dogs),
                len(reports),
                len(adoptions),
                len(reclaims),
                len(vaccinations),
                len(penalties),
                len(notifications),
            )
        )

    def _get_or_create_admin(self, password):
        admin = CustomUser.objects.filter(email="admin@bayawan.local").first()
        if admin:
            return admin
        admin = CustomUser.objects.create_superuser(
            username="admin",
            email="admin@bayawan.local",
            password=password,
            legal_consent=True,
            legal_consented_at=timezone.now(),
        )
        admin.role = CustomUser.Roles.ADMIN
        admin.email_verified = True
        admin.is_verified = True
        admin.save(update_fields=["role", "email_verified", "is_verified"])
        return admin

    def _get_or_create_staff(self, password):
        staff = CustomUser.objects.filter(email="staff@bayawan.local").first()
        if staff:
            return staff
        staff = CustomUser.objects.create_user(
            username="staff",
            email="staff@bayawan.local",
            password=password,
            is_staff=True,
            legal_consent=True,
            legal_consented_at=timezone.now(),
        )
        staff.role = CustomUser.Roles.STAFF
        staff.email_verified = True
        staff.is_verified = True
        staff.save(update_fields=["role", "email_verified", "is_verified"])
        return staff

    def _get_or_create_owners(self, count, password):
        owners = []
        for idx in range(1, count + 1):
            email = f"user{idx}@bayawan.local"
            user = CustomUser.objects.filter(email=email).first()
            if not user:
                user = CustomUser.objects.create_user(
                    username=f"user{idx}",
                    email=email,
                    password=password,
                    legal_consent=True,
                    legal_consented_at=timezone.now(),
                )
                user.email_verified = True
                user.is_verified = True
                user.save(update_fields=["email_verified", "is_verified"])
            owners.append(user)
        return owners

    def _create_dogs(self, count, owners):
        names = ["Lucky", "Max", "Bella", "Coco", "Milo", "Rocky", "Luna", "Buddy", "Zara", "Nala"]
        colors = ["Brown", "Black", "White", "Tan", "Spotted"]
        statuses = [choice for choice, _ in Dog.Status.choices]
        dogs = []
        for i in range(count):
            owner = random.choice(owners + [None])
            dog = Dog.objects.create(
                owner=owner,
                name=random.choice(names),
                status=random.choice(statuses),
                sex=random.choice(["Male", "Female"]),
                color=random.choice(colors),
            )
            dogs.append(dog)
        return dogs

    def _create_reports(self, count, owners):
        report_types = [choice for choice, _ in Report.ReportType.choices]
        locations = ["Poblacion", "Ubogon", "Pagatban", "Bayawan City Proper", "Villareal"]
        reports = []
        for _ in range(count):
            reports.append(
                Report.objects.create(
                    report_type=random.choice(report_types),
                    reported_by=random.choice(owners + [None]),
                    location=random.choice(locations),
                    description="Sample report description.",
                )
            )
        return reports

    def _create_adoptions(self, count, owners, dogs):
        if not owners or not dogs:
            return []
        statuses = [choice for choice, _ in AdoptionReservation.Status.choices]
        adoptions = []
        for _ in range(count):
            adoptions.append(
                AdoptionReservation.objects.create(
                    dog=random.choice(dogs),
                    requester=random.choice(owners),
                    status=random.choice(statuses),
                )
            )
        return adoptions

    def _create_reclaims(self, count, dogs):
        dogs_with_owner = [dog for dog in dogs if dog.owner_id]
        if not dogs_with_owner:
            return []
        statuses = [choice for choice, _ in ReclaimRequest.Status.choices]
        reclaims = []
        for _ in range(count):
            dog = random.choice(dogs_with_owner)
            reclaims.append(
                ReclaimRequest.objects.create(
                    dog=dog,
                    owner=dog.owner,
                    status=random.choice(statuses),
                )
            )
        return reclaims

    def _create_vaccinations(self, count, dogs):
        if not dogs:
            return []
        vaccines = ["Rabies", "DHPP", "Leptospirosis"]
        records = []
        today = date.today()
        for _ in range(count):
            vaccinated = today - timedelta(days=random.randint(1, 120))
            expires = vaccinated + timedelta(days=365)
            records.append(
                VaccinationRecord.objects.create(
                    dog=random.choice(dogs),
                    vaccine_type=random.choice(vaccines),
                    vaccinated_date=vaccinated,
                    expiration_date=expires,
                )
            )
        return records

    def _create_penalties(self, count, dogs):
        if not dogs:
            return []
        checklist = PenaltyChecklistItem.objects.first()
        if not checklist:
            checklist = PenaltyChecklistItem.objects.create(
                code="SEED-001",
                section=PenaltyChecklistItem.Section.SECTION_28,
                description="Seeded violation",
                default_amount=100,
            )
        cases = []
        for _ in range(count):
            dog = random.choice(dogs)
            owner = dog.owner
            if not owner:
                continue
            case = PenaltyCase.objects.create(dog=dog, owner=owner, total_amount=checklist.default_amount)
            PenaltyLineItem.objects.create(
                case=case,
                checklist_item=checklist,
                description=checklist.description,
                quantity=1,
                unit_amount=checklist.default_amount,
                total=checklist.default_amount,
            )
            cases.append(case)
        return cases

    def _create_notifications(self, count, owners, admin, staff):
        users = [admin, staff] + owners
        notifications = []
        for _ in range(count):
            user = random.choice(users)
            notifications.append(
                Notification.objects.create(
                    user=user,
                    title="Seeded notification",
                    message="This is a demo notification.",
                    action_url="",
                )
            )
        return notifications
