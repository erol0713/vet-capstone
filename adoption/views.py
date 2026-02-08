from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.urls import reverse

from dogs.models import Dog
from notifications.models import Notification
from penalties.models import PenaltyCase
from users.decorators import role_required, verified_required

from .forms import AdoptionReservationForm, AdoptionScheduleForm, ReclaimRequestForm
from .models import AdoptionReservation, ReclaimRequest

RECLAIM_WINDOW_DAYS = 3


def notify_staff(title: str, message: str) -> None:
    User = get_user_model()
    recipients = User.objects.filter(role__in=['ADMIN', 'STAFF'])
    if not recipients.exists():
        return
    staff_queue_url = reverse('adoption_staff_queue')
    Notification.objects.bulk_create(
        [
            Notification(user=user, title=title, message=message, action_url=staff_queue_url)
            for user in recipients
        ]
    )


def reclaim_window_elapsed(dog: Dog, now=None) -> bool:
    if not dog.capture_datetime:
        return False
    now = now or timezone.now()
    deadline = dog.capture_datetime + timezone.timedelta(days=RECLAIM_WINDOW_DAYS)
    return now >= deadline


def has_active_reclaim(dog: Dog) -> bool:
    return (
        ReclaimRequest.objects.filter(dog=dog)
        .exclude(status=ReclaimRequest.Status.REJECTED)
        .exists()
    )


def has_active_adoption_request(dog: Dog, user) -> bool:
    return (
        AdoptionReservation.objects.filter(dog=dog, requester=user)
        .exclude(status__in=(AdoptionReservation.Status.REJECTED, AdoptionReservation.Status.CANCELLED))
        .exists()
    )


def has_active_reclaim_request_for_owner(dog: Dog, owner) -> bool:
    return (
        ReclaimRequest.objects.filter(dog=dog, owner=owner)
        .exclude(status=ReclaimRequest.Status.REJECTED)
        .exists()
    )


def notify_reservation_eligibility(reservations) -> None:
    now = timezone.now()
    to_update = []
    notifications = []
    my_requests_url = reverse('adoption_my_requests')
    for reservation in reservations:
        if reservation.status != AdoptionReservation.Status.PENDING:
            continue
        if reservation.confirmed_at or reservation.eligibility_notified_at:
            continue
        dog = reservation.dog
        if dog.status in (Dog.Status.ADOPTED, Dog.Status.RECLAIMED, Dog.Status.RELEASED):
            continue
        if dog.status == Dog.Status.AVAILABLE and not dog.capture_datetime:
            reservation.eligibility_notified_at = now
            to_update.append(reservation)
            notifications.append(
                Notification(
                    user=reservation.requester,
                    title='Adoption reservation ready',
                    message=(
                        f'Your reservation for dog #{dog.pk} is ready. '
                        'Please confirm to proceed.'
                    ),
                    action_url=my_requests_url,
                )
            )
            continue
        if not reclaim_window_elapsed(dog, now=now):
            continue
        if has_active_reclaim(dog):
            continue
        reservation.eligibility_notified_at = now
        to_update.append(reservation)
        notifications.append(
            Notification(
                user=reservation.requester,
                title='Adoption reservation ready',
                message=(
                    f'Your reservation for dog #{dog.pk} is now eligible for adoption. '
                    'Please confirm to proceed.'
                ),
                action_url=my_requests_url,
            )
        )
    if to_update:
        AdoptionReservation.objects.bulk_update(to_update, ['eligibility_notified_at'])
    if notifications:
        Notification.objects.bulk_create(notifications)


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
    eligible_statuses = {Dog.Status.AVAILABLE, Dog.Status.IMPOUNDED}
    if dog.status not in eligible_statuses:
        messages.warning(request, 'This dog is not available for adoption.')
        return redirect('dogs_public_detail', pk=dog.pk)
    if dog.status == Dog.Status.IMPOUNDED and not dog.capture_datetime:
        messages.warning(request, 'This dog is not eligible for adoption yet.')
        return redirect('dogs_public_detail', pk=dog.pk)
    if has_active_adoption_request(dog, request.user):
        messages.warning(request, 'You already have an active adoption request for this dog.')
        return redirect('adoption_my_requests')
    form = AdoptionReservationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        reservation = form.save(commit=False)
        reservation.dog = dog
        reservation.requester = request.user
        reservation.status = AdoptionReservation.Status.PENDING
        reservation.save()
        if dog.status == Dog.Status.AVAILABLE and not dog.capture_datetime:
            reservation.eligibility_notified_at = timezone.now()
            reservation.save(update_fields=['eligibility_notified_at'])
        notify_staff(
            'New adoption request',
            f'Reservation #{reservation.pk} for dog #{dog.pk} by {request.user.email}.',
        )
        messages.success(request, 'Adoption reservation submitted.')
        return redirect('adoption_my_requests')
    reclaim_deadline = None
    if dog.capture_datetime:
        reclaim_deadline = dog.capture_datetime + timezone.timedelta(days=RECLAIM_WINDOW_DAYS)
    return render(
        request,
        'adoption/reserve.html',
        {'form': form, 'dog': dog, 'reclaim_deadline': reclaim_deadline},
    )


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
    if has_active_reclaim_request_for_owner(dog, request.user):
        messages.warning(request, 'You already have an active reclaim request for this dog.')
        return redirect('adoption_my_requests')
    if has_active_reclaim(dog):
        messages.warning(request, 'This dog already has an active reclaim request.')
        return redirect('dogs_public_detail', pk=dog.pk)
    form = ReclaimRequestForm(request.POST or None, request.FILES or None)
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
    adoptions = (
        AdoptionReservation.objects.filter(requester=request.user)
        .select_related('dog', 'requester')
        .order_by('-created_at')
    )
    notify_reservation_eligibility(adoptions)
    reclaims = ReclaimRequest.objects.filter(owner=request.user).order_by('-created_at')
    return render(
        request,
        'adoption/my_requests.html',
        {'adoptions': adoptions, 'reclaims': reclaims},
    )


@login_required
@role_required('ADMIN', 'STAFF')
def staff_queue(request):
    adoptions = AdoptionReservation.objects.select_related('dog', 'requester').order_by('-created_at')
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
@verified_required
def confirm_adoption_reservation(request, pk: int):
    reservation = get_object_or_404(AdoptionReservation, pk=pk, requester=request.user)
    if request.method != 'POST':
        messages.info(request, 'Use the confirm button to proceed with adoption.')
        return redirect('adoption_my_requests')
    if reservation.status != AdoptionReservation.Status.PENDING:
        messages.warning(request, 'This reservation cannot be confirmed.')
        return redirect('adoption_my_requests')
    if reservation.confirmed_at:
        messages.info(request, 'This reservation is already confirmed.')
        return redirect('adoption_my_requests')
    if reservation.dog.capture_datetime:
        if not reclaim_window_elapsed(reservation.dog):
            messages.warning(request, 'Reclaim window has not ended yet.')
            return redirect('adoption_my_requests')
        if has_active_reclaim(reservation.dog):
            messages.warning(request, 'This dog has an active reclaim request.')
            return redirect('adoption_my_requests')
    reservation.confirmed_at = timezone.now()
    reservation.save(update_fields=['confirmed_at'])
    notify_staff(
        'Adoption reservation confirmed',
        f'Reservation #{reservation.pk} for dog #{reservation.dog_id} was confirmed.',
    )
    messages.success(request, 'Reservation confirmed. Staff will schedule your appointment.')
    return redirect('adoption_my_requests')


@login_required
@role_required('ADMIN', 'STAFF')
def schedule_adoption(request, pk: int):
    reservation = get_object_or_404(AdoptionReservation, pk=pk)
    if request.method != 'POST':
        return redirect('adoption_staff_queue')
    if reservation.status in (
        AdoptionReservation.Status.REJECTED,
        AdoptionReservation.Status.CANCELLED,
        AdoptionReservation.Status.COMPLETED,
    ):
        messages.warning(request, 'This reservation cannot be scheduled.')
        return redirect('adoption_staff_queue')
    if not reservation.confirmed_at:
        messages.warning(request, 'Wait for the user to confirm before scheduling.')
        return redirect('adoption_staff_queue')
    form = AdoptionScheduleForm(request.POST)
    if not form.is_valid():
        messages.error(request, 'Enter a valid appointment date and time.')
        return redirect('adoption_staff_queue')
    reservation.appointment_schedule = form.cleaned_data['appointment_schedule']
    update_fields = ['appointment_schedule']
    if reservation.status == AdoptionReservation.Status.PENDING:
        reservation.status = AdoptionReservation.Status.APPROVED
        update_fields.append('status')
    reservation.save(update_fields=update_fields)
    schedule = (
        timezone.localtime(reservation.appointment_schedule)
        if timezone.is_aware(reservation.appointment_schedule)
        else reservation.appointment_schedule
    )
    Notification.objects.create(
        user=reservation.requester,
        title='Adoption appointment scheduled',
        message=(
            f'Your adoption appointment for dog #{reservation.dog_id} is set for '
            f'{schedule:%b %d, %Y %I:%M %p}.'
        ),
        action_url=reverse('adoption_my_requests'),
    )
    messages.success(request, 'Adoption appointment scheduled.')
    return redirect('adoption_staff_queue')


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
