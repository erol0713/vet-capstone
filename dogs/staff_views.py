from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme

from notifications.models import Notification
from users.decorators import role_required

from .forms import DogForm, VaccinationRecordForm, VaccinationScheduleForm
from .models import Dog
from .services import apply_intake_status, latest_vaccination_record


@login_required
@role_required('ADMIN', 'STAFF')
def manage_list(request):
    dogs = Dog.objects.order_by('-created_at')
    return render(request, 'dogs/manage_list.html', {'dogs': dogs})


@login_required
@role_required('ADMIN', 'STAFF')
def registered_by_owner(request):
    dogs = (
        Dog.objects.select_related('owner')
        .filter(
            owner__isnull=False,
            capture_datetime__isnull=True,
            surrender_datetime__isnull=True,
        )
        .order_by('owner__username', 'name')
    )
    grouped = {}
    for dog in dogs:
        grouped.setdefault(dog.owner, []).append(dog)
    return render(request, 'dogs/registered_by_owner.html', {'grouped': grouped})


@login_required
@role_required('ADMIN', 'STAFF')
def registered_detail(request, pk: int):
    dog = get_object_or_404(
        Dog.objects.select_related('owner'),
        pk=pk,
        owner__isnull=False,
        capture_datetime__isnull=True,
        surrender_datetime__isnull=True,
    )
    if request.method == 'POST':
        action = request.POST.get('action', '').strip().lower()
        if action == 'approve':
            can_approve = dog.vaccination_status == Dog.VaccinationStatus.VACCINATED and (
                bool(dog.vaccination_proof) or dog.vaccinations.exists()
            )
            if can_approve:
                dog.registration_approval_status = Dog.RegistrationApprovalStatus.APPROVED
                dog.registration_reviewed_at = timezone.now()
                dog.registration_reviewed_by = request.user
                dog.save(
                    update_fields=[
                        'registration_approval_status',
                        'registration_reviewed_at',
                        'registration_reviewed_by',
                    ]
                )
                Notification.objects.create(
                    user=dog.owner,
                    title='Dog Registration Approved',
                    message=(
                        f'Your dog "{dog.name or "Unnamed Dog"}" registration is approved and now visible in My Dogs.'
                    ),
                    action_url=reverse('profile'),
                )
                messages.success(request, 'Registration approved.')
            else:
                messages.error(
                    request,
                    'Approval requires a verified vaccination proof or a recorded vaccination entry.',
                )
        elif action == 'reject':
            dog.registration_approval_status = Dog.RegistrationApprovalStatus.REJECTED
            dog.registration_reviewed_at = timezone.now()
            dog.registration_reviewed_by = request.user
            dog.save(
                update_fields=[
                    'registration_approval_status',
                    'registration_reviewed_at',
                    'registration_reviewed_by',
                ]
            )
            Notification.objects.create(
                user=dog.owner,
                title='Dog Registration Needs Update',
                message=(
                    f'Your dog "{dog.name or "Unnamed Dog"}" registration was not approved. '
                    'Please coordinate with the veterinary office for requirements.'
                ),
                action_url=reverse('profile'),
            )
            messages.success(request, 'Registration marked as rejected.')
        return redirect('dogs_registered_detail', pk=dog.pk)
    latest_record = latest_vaccination_record(dog)
    is_vaccine_expired = bool(
        latest_record
        and latest_record.expiration_date
        and latest_record.expiration_date < timezone.localdate()
    )
    return render(
        request,
        'dogs/registered_detail.html',
        {
            'dog': dog,
            'latest_vaccination': latest_record,
            'is_vaccine_expired': is_vaccine_expired,
        },
    )


@login_required
@role_required('ADMIN', 'STAFF')
def vaccination_requests(request):
    dogs = (
        Dog.objects.select_related('owner')
        .filter(
            owner__isnull=False,
            capture_datetime__isnull=True,
            surrender_datetime__isnull=True,
            vaccination_status=Dog.VaccinationStatus.UNVACCINATED,
            vaccination_request=True,
        )
        .order_by('owner__username', 'name')
    )
    return render(request, 'dogs/vaccination_requests.html', {'dogs': dogs})


@login_required
@role_required('ADMIN', 'STAFF')
def record_vaccination(request, pk: int):
    dog = get_object_or_404(
        Dog.objects.select_related('owner'),
        pk=pk,
        owner__isnull=False,
        capture_datetime__isnull=True,
        surrender_datetime__isnull=True,
    )
    form = VaccinationRecordForm(request.POST or None)
    latest_record = latest_vaccination_record(dog)
    today = timezone.localdate()
    if request.method == 'POST' and form.is_valid():
        record = form.save(commit=False)
        record.dog = dog
        record.save()
        dog.vaccination_status = Dog.VaccinationStatus.VACCINATED
        dog.vaccination_request = False
        dog.vaccination_schedule = None
        dog.registration_approval_status = Dog.RegistrationApprovalStatus.APPROVED
        dog.registration_reviewed_at = timezone.now()
        dog.registration_reviewed_by = request.user
        dog.save(
            update_fields=[
                'vaccination_status',
                'vaccination_request',
                'vaccination_schedule',
                'registration_approval_status',
                'registration_reviewed_at',
                'registration_reviewed_by',
            ]
        )
        if dog.owner and record.expiration_date:
            action_url = reverse('dogs_owner_detail', kwargs={'pk': dog.pk})
            if record.expiration_date <= today:
                if record.expiration_date < today:
                    message = (
                        f'Your dog "{dog.name or "Unnamed Dog"}" has an expired vaccine record '
                        f'(expired on {record.expiration_date:%b %d, %Y}). '
                        'Request a new vaccination schedule.'
                    )
                else:
                    message = (
                        f'Your dog "{dog.name or "Unnamed Dog"}" vaccine expires today '
                        f'({record.expiration_date:%b %d, %Y}). '
                        'Request a new vaccination schedule if renewal is needed.'
                    )
                Notification.objects.create(
                    user=dog.owner,
                    title='Vaccine Expired',
                    message=message,
                    action_url=action_url,
                )
                record.notified_on_expiry = True
                record.save(update_fields=['notified_on_expiry'])
            else:
                vacc_date_text = (
                    f'Vaccinated on {record.vaccinated_date:%b %d, %Y}'
                    if record.vaccinated_date
                    else 'Owner proof was verified by staff'
                )
                Notification.objects.create(
                    user=dog.owner,
                    title='Vaccination Recorded',
                    message=(
                        f'Vaccination details for "{dog.name or "Unnamed Dog"}" were updated. '
                        f'{vacc_date_text}. Expires on {record.expiration_date:%b %d, %Y}.'
                    ),
                    action_url=action_url,
                )
        messages.success(request, 'Vaccination details recorded successfully.')
        return redirect('dogs_registered_detail', pk=dog.pk)
    return render(
        request,
        'dogs/record_vaccination.html',
        {'dog': dog, 'form': form, 'latest_vaccination': latest_record},
    )


@login_required
@role_required('ADMIN', 'STAFF')
def schedule_vaccination(request, pk: int):
    dog = get_object_or_404(
        Dog,
        pk=pk,
        owner__isnull=False,
        capture_datetime__isnull=True,
        surrender_datetime__isnull=True,
        vaccination_status=Dog.VaccinationStatus.UNVACCINATED,
        vaccination_request=True,
    )
    form = VaccinationScheduleForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        dog.vaccination_schedule = form.cleaned_data['vaccination_schedule']
        dog.save(update_fields=['vaccination_schedule'])
        schedule = (
            timezone.localtime(dog.vaccination_schedule)
            if timezone.is_aware(dog.vaccination_schedule)
            else dog.vaccination_schedule
        )
        Notification.objects.create(
            user=dog.owner,
            title='Vaccination Appointment Scheduled',
            message=(
                f'Your dog "{dog.name or "Unnamed Dog"}" has a vaccination appointment '
                f'on {schedule:%b %d, %Y %I:%M %p}.'
            ),
            action_url=reverse('profile'),
        )
        messages.success(request, 'Vaccination appointment scheduled.')
        return redirect('dogs_registered_by_owner')
    return render(request, 'dogs/schedule_vaccination.html', {'dog': dog, 'form': form})


@login_required
@role_required('ADMIN', 'STAFF')
def create_dog(request):
    form = DogForm(request.POST or None, request.FILES or None)
    if request.method == 'POST':
        if form.is_valid():
            dog = form.save(commit=False)
            apply_intake_status(dog)
            dog.registration_approval_status = Dog.RegistrationApprovalStatus.APPROVED
            dog.registration_reviewed_at = timezone.now()
            dog.registration_reviewed_by = request.user
            dog.save()
            if (
                dog.owner
                and dog.vaccination_status == Dog.VaccinationStatus.UNVACCINATED
                and dog.vaccination_request
                and dog.vaccination_schedule
            ):
                schedule = (
                    timezone.localtime(dog.vaccination_schedule)
                    if timezone.is_aware(dog.vaccination_schedule)
                    else dog.vaccination_schedule
                )
                Notification.objects.create(
                    user=dog.owner,
                    title='Vaccination Appointment Scheduled',
                    message=(
                        f'Your dog "{dog.name or "Unnamed Dog"}" has a vaccination appointment '
                        f'on {schedule:%b %d, %Y %I:%M %p}.'
                    ),
                    action_url=reverse('profile'),
                )
            messages.success(request, f'Dog #{dog.pk} created.')
            return redirect('dogs_manage_list')
        messages.error(
            request,
            'Unable to create intake record. Please fix the highlighted fields and try again.',
        )
    return render(
        request,
        'dogs/form.html',
        {
            'form': form,
            'title': 'Create Dog',
            'dog': None,
            'show_vaccination_fields': False,
        },
    )


@login_required
@role_required('ADMIN', 'STAFF')
def edit_dog(request, pk: int):
    dog = get_object_or_404(Dog, pk=pk)
    form = DogForm(request.POST or None, request.FILES or None, instance=dog)
    next_url = request.POST.get('next') or request.GET.get('next')
    if next_url and not url_has_allowed_host_and_scheme(
        url=next_url,
        allowed_hosts={request.get_host()},
    ):
        next_url = None
    if request.method == 'POST':
        if form.is_valid():
            dog = form.save(commit=False)
            apply_intake_status(dog)
            dog.save()
            messages.success(request, f'Dog #{dog.pk} updated.')
            return redirect(next_url or 'dogs_manage_list')
        messages.error(
            request,
            'Unable to update intake record. Please fix the highlighted fields and try again.',
        )
    return render(
        request,
        'dogs/form.html',
        {
            'form': form,
            'title': f'Edit Dog #{dog.pk}',
            'dog': dog,
            'show_vaccination_fields': False,
            'next_url': next_url,
        },
    )


@login_required
@role_required('ADMIN', 'STAFF')
def delete_dog(request, pk: int):
    dog = get_object_or_404(Dog, pk=pk)
    if request.method != 'POST':
        messages.info(request, 'Use the delete button to remove a dog.')
        return redirect('dogs_edit', pk=dog.pk)
    dog.delete()
    messages.success(request, 'Dog deleted.')
    return redirect('dogs_manage_list')
