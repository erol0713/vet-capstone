from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from adoption.models import AdoptionReservation, ReclaimRequest
from dogs.models import Dog
from penalties.models import PenaltyCase
from reports.models import Report
from vaccinations.models import VaccinationRecord

from .models import DailyMetric


def increment_metric(metric: str, delta: int = 1) -> None:
    today = timezone.localdate()
    obj, _ = DailyMetric.objects.get_or_create(date=today, metric=metric)
    obj.value = obj.value + delta
    obj.save(update_fields=['value'])


@receiver(post_save, sender=Dog)
def track_dog_created(sender, instance: Dog, created: bool, **kwargs) -> None:
    if created:
        increment_metric('dogs_created', 1)


@receiver(post_save, sender=Report)
def track_report_created(sender, instance: Report, created: bool, **kwargs) -> None:
    if created:
        increment_metric('reports_created', 1)


@receiver(post_save, sender=AdoptionReservation)
def track_adoption_status(sender, instance: AdoptionReservation, created: bool, **kwargs) -> None:
    if created:
        increment_metric('adoption_requests', 1)
    if instance.status == AdoptionReservation.Status.COMPLETED:
        increment_metric('adoptions_completed', 1)


@receiver(post_save, sender=ReclaimRequest)
def track_reclaim_status(sender, instance: ReclaimRequest, created: bool, **kwargs) -> None:
    if created:
        increment_metric('reclaim_requests', 1)
    if instance.status == ReclaimRequest.Status.COMPLETED:
        increment_metric('reclaims_completed', 1)


@receiver(post_save, sender=PenaltyCase)
def track_penalty_case(sender, instance: PenaltyCase, created: bool, **kwargs) -> None:
    if created:
        increment_metric('penalty_cases', 1)
    if instance.is_finalized:
        increment_metric('penalties_finalized', 1)


@receiver(post_save, sender=VaccinationRecord)
def track_vaccination(sender, instance: VaccinationRecord, created: bool, **kwargs) -> None:
    if created:
        increment_metric('vaccinations_recorded', 1)
