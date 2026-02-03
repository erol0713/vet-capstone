from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from dogs.models import Dog
from notifications.models import Notification
from penalties.models import PenaltyCase
from users.decorators import role_required, verified_required

from .forms import AdoptionReservationForm, ReclaimRequestForm
from .models import AdoptionReservation, ReclaimRequest


def notify_staff(title: str, message: str) -> None:
    User = get_user_model()
    recipients = User.objects.filter(role__in=['ADMIN', 'STAFF'])
    if not recipients.exists():
        return
    Notification.objects.bulk_create(
        [Notification(user=user, title=title, message=message) for user in recipients]
    )


def ensure_penalty_case(dog: Dog, owner) -> tuple[PenaltyCase, bool]:
    existing = (
        PenaltyCase.objects.filter(dog=dog, owner=owner, is_finalized=False)
        .order_by('-created_at')
        .first()
    )
    if existing:
        return existing, False
    return PenaltyCase.objects.create(dog=dog, owner=owner), True


@login_required
@verified_required
def reserve_adoption(request, dog_id: int):
    dog = get_object_or_404(Dog, pk=dog_id)
    if dog.status != Dog.Status.AVAILABLE:
        messages.warning(request, 'This dog is not available for adoption.')
        return redirect('dogs_public_detail', pk=dog.pk)
    form = AdoptionReservationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        reservation = form.save(commit=False)
        reservation.dog = dog
        reservation.requester = request.user
        reservation.status = AdoptionReservation.Status.PENDING
        reservation.save()
        notify_staff(
            'New adoption request',
            f'Reservation #{reservation.pk} for dog #{dog.pk} by {request.user.email}.',
        )
        messages.success(request, 'Adoption reservation submitted.')
        return redirect('adoption_my_requests')
    return render(request, 'adoption/reserve.html', {'form': form, 'dog': dog})


@login_required
@verified_required
def request_reclaim(request, dog_id: int):
    dog = get_object_or_404(Dog, pk=dog_id)
    eligible_statuses = {Dog.Status.IMPOUNDED, Dog.Status.AVAILABLE}
    if not dog.capture_datetime:
        messages.warning(request, 'This dog is not eligible for reclaim.')
        return redirect('dogs_public_detail', pk=dog.pk)
    if dog.status not in eligible_statuses:
        messages.warning(
            request,
            f'This dog is marked as {dog.get_status_display()} and cannot be reclaimed.',
        )
        return redirect('dogs_public_detail', pk=dog.pk)
    form = ReclaimRequestForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        reclaim = form.save(commit=False)
        reclaim.dog = dog
        reclaim.owner = request.user
        reclaim.status = ReclaimRequest.Status.PENDING
        reclaim.save()
        penalty_case, created = ensure_penalty_case(dog, request.user)
        notify_staff(
            'New reclaim request',
            (
                f'Reclaim #{reclaim.pk} for dog #{dog.pk} by {request.user.email}. '
                f'Penalty case #{penalty_case.pk}.'
            ),
        )
        messages.success(request, 'Reclaim request submitted.')
        return redirect('adoption_my_requests')
    return render(request, 'adoption/reclaim.html', {'form': form, 'dog': dog})


@login_required
def my_requests(request):
    adoptions = AdoptionReservation.objects.filter(requester=request.user).order_by('-created_at')
    reclaims = ReclaimRequest.objects.filter(owner=request.user).order_by('-created_at')
    return render(
        request,
        'adoption/my_requests.html',
        {'adoptions': adoptions, 'reclaims': reclaims},
    )


@login_required
@role_required('ADMIN', 'STAFF')
def staff_queue(request):
    adoptions = AdoptionReservation.objects.order_by('-created_at')
    reclaims = ReclaimRequest.objects.select_related('dog', 'owner').order_by('-created_at')
    case_map = {}
    if reclaims:
        dog_ids = [item.dog_id for item in reclaims]
        owner_ids = [item.owner_id for item in reclaims]
        cases = (
            PenaltyCase.objects.filter(dog_id__in=dog_ids, owner_id__in=owner_ids)
            .order_by('-created_at')
        )
        for case in cases:
            key = (case.dog_id, case.owner_id)
            if key not in case_map:
                case_map[key] = case
        for reclaim in reclaims:
            reclaim.penalty_case = case_map.get((reclaim.dog_id, reclaim.owner_id))
    return render(
        request,
        'adoption/staff_queue.html',
        {'adoptions': adoptions, 'reclaims': reclaims},
    )


@login_required
@role_required('ADMIN', 'STAFF')
def update_adoption_status(request, pk: int, status: str):
    reservation = get_object_or_404(AdoptionReservation, pk=pk)
    if status in AdoptionReservation.Status.values:
        reservation.status = status
        reservation.save(update_fields=['status'])
        if status == AdoptionReservation.Status.COMPLETED:
            Dog.objects.filter(id=reservation.dog_id).update(status=Dog.Status.ADOPTED)
        messages.success(request, f'Adoption marked as {reservation.get_status_display()}.')
    return redirect('adoption_staff_queue')


@login_required
@role_required('ADMIN', 'STAFF')
def update_reclaim_status(request, pk: int, status: str):
    reclaim = get_object_or_404(ReclaimRequest, pk=pk)
    if status in ReclaimRequest.Status.values:
        reclaim.status = status
        if status in (ReclaimRequest.Status.APPROVED, ReclaimRequest.Status.COMPLETED):
            reclaim.approved_by = request.user
        reclaim.save(update_fields=['status', 'approved_by'])
        if status == ReclaimRequest.Status.COMPLETED:
            Dog.objects.filter(id=reclaim.dog_id).update(
                status=Dog.Status.RECLAIMED,
                owner=reclaim.owner,
            )
            penalty_case, _ = ensure_penalty_case(reclaim.dog, reclaim.owner)
            if not penalty_case.reclaimed_at:
                penalty_case.reclaimed_at = timezone.now()
                penalty_case.save(update_fields=['reclaimed_at'])
            notify_staff(
                'Reclaim completed',
                (
                    f'Reclaim #{reclaim.pk} completed for dog #{reclaim.dog_id}. '
                    f'Penalty case #{penalty_case.pk} ready.'
                ),
            )
        messages.success(request, f'Reclaim marked as {reclaim.get_status_display()}.')
    return redirect('adoption_staff_queue')
