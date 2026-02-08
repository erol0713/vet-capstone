from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils import timezone
from django.urls import reverse

from users.decorators import role_required, verified_required
from notifications.models import Notification

from .forms import DogForm, UserDogRegistrationForm, VaccinationScheduleForm
from .models import Dog


def public_list(request):
    dogs = Dog.objects.filter(
        status__in=[Dog.Status.IMPOUNDED, Dog.Status.AVAILABLE],
    ).order_by('-created_at')
    return render(request, 'dogs/public_list.html', {'dogs': dogs})


def apply_intake_status(dog: Dog) -> None:
    if dog.capture_datetime or dog.surrender_datetime or not dog.owner:
        if dog.surrender_datetime:
            dog.status = Dog.Status.AVAILABLE
        else:
            dog.status = Dog.Status.IMPOUNDED


def public_detail(request, pk: int):
    dog = get_object_or_404(Dog, pk=pk)
    can_reclaim = dog.capture_datetime and dog.status in (Dog.Status.IMPOUNDED, Dog.Status.AVAILABLE)
    can_adopt = dog.status == Dog.Status.AVAILABLE
    can_reserve = dog.capture_datetime and dog.status in (Dog.Status.IMPOUNDED, Dog.Status.AVAILABLE)
    return render(
        request,
        'dogs/public_detail.html',
        {
            'dog': dog,
            'can_reclaim': can_reclaim,
            'can_adopt': can_adopt,
            'can_reserve': can_reserve,
        },
    )


@login_required
@verified_required
def register_dog(request):
    form = UserDogRegistrationForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        dog = form.save(commit=False)
        dog.owner = request.user
        dog.status = Dog.Status.RELEASED
        dog.save()
        messages.success(request, 'Dog registered successfully.')
        return redirect('profile')
    return render(request, 'dogs/register.html', {'form': form})


@login_required
@verified_required
def delete_registered_dog(request, pk: int):
    dog = get_object_or_404(
        Dog,
        pk=pk,
        owner=request.user,
        capture_datetime__isnull=True,
        surrender_datetime__isnull=True,
    )
    if request.method != 'POST':
        messages.info(request, 'Use the delete button to remove a registered dog.')
        return redirect('profile')
    dog.delete()
    messages.success(request, 'Registered dog removed.')
    return redirect('profile')


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
    return render(request, 'dogs/registered_detail.html', {'dog': dog})


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
    if request.method == 'POST' and form.is_valid():
        dog = form.save(commit=False)
        apply_intake_status(dog)
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
    if request.method == 'POST' and form.is_valid():
        dog = form.save(commit=False)
        apply_intake_status(dog)
        dog.save()
        messages.success(request, f'Dog #{dog.pk} updated.')
        return redirect(next_url or 'dogs_manage_list')
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
