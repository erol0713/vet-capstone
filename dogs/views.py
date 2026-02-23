from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from users.decorators import verified_required
from vaccinations.models import VaccinationRecord

from .forms import UserDogRegistrationForm
from .models import Dog
from .services import latest_vaccination_record, notify_vaccination_staff


def public_list(request):
    dogs = Dog.objects.filter(
        status__in=[Dog.Status.IMPOUNDED, Dog.Status.AVAILABLE],
    ).order_by('-created_at')
    return render(request, 'dogs/public_list.html', {'dogs': dogs})


def public_detail(request, pk: int):
    dog = get_object_or_404(
        Dog.objects.filter(status__in=[Dog.Status.IMPOUNDED, Dog.Status.AVAILABLE]),
        pk=pk,
    )
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
        dog.registration_approval_status = Dog.RegistrationApprovalStatus.PENDING
        dog.registration_reviewed_at = None
        dog.registration_reviewed_by = None
        dog.save()
        messages.success(
            request,
            'Dog registration submitted. It will appear in My Dogs after admin/staff approval.',
        )
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
    referer = request.META.get('HTTP_REFERER', '')
    redirect_to = 'profile' if 'profile' in referer else 'dogs_my_dogs'
    if request.method != 'POST':
        messages.info(request, 'Use the delete button to remove a registered dog.')
        return redirect(redirect_to)
    dog.delete()
    messages.success(request, 'Registered dog removed.')
    return redirect(redirect_to)


@login_required
def my_dogs(request):
    registered_dogs = (
        Dog.objects.filter(
            owner=request.user,
            capture_datetime__isnull=True,
            surrender_datetime__isnull=True,
            registration_approval_status=Dog.RegistrationApprovalStatus.APPROVED,
        )
        .prefetch_related(
            Prefetch(
                'vaccinations',
                queryset=VaccinationRecord.objects.order_by('-expiration_date', '-created_at'),
                to_attr='vaccination_records_cache',
            )
        )
        .order_by('-created_at')
    )
    for dog in registered_dogs:
        dog.latest_vaccination = (
            dog.vaccination_records_cache[0] if dog.vaccination_records_cache else None
        )
    return render(request, 'dogs/my_dogs.html', {'registered_dogs': registered_dogs})


@login_required
def owner_detail(request, pk: int):
    dog = get_object_or_404(
        Dog,
        pk=pk,
        owner=request.user,
        capture_datetime__isnull=True,
        surrender_datetime__isnull=True,
        registration_approval_status=Dog.RegistrationApprovalStatus.APPROVED,
    )
    latest_record = latest_vaccination_record(dog)
    is_vaccine_expired = bool(
        latest_record
        and latest_record.expiration_date
        and latest_record.expiration_date < timezone.localdate()
    )
    form = UserDogRegistrationForm(instance=dog)
    return render(
        request,
        'dogs/owner_detail.html',
        {
            'dog': dog,
            'latest_vaccination': latest_record,
            'is_vaccine_expired': is_vaccine_expired,
            'form': form,
            'open_edit_modal': False,
        },
    )


@login_required
@verified_required
def owner_edit(request, pk: int):
    dog = get_object_or_404(
        Dog,
        pk=pk,
        owner=request.user,
        capture_datetime__isnull=True,
        surrender_datetime__isnull=True,
        registration_approval_status=Dog.RegistrationApprovalStatus.APPROVED,
    )
    form = UserDogRegistrationForm(request.POST or None, request.FILES or None, instance=dog)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, 'Dog profile updated.')
            return redirect('dogs_owner_detail', pk=dog.pk)
        latest_record = latest_vaccination_record(dog)
        return render(
            request,
            'dogs/owner_detail.html',
            {
                'dog': dog,
                'latest_vaccination': latest_record,
                'is_vaccine_expired': bool(
                    latest_record
                    and latest_record.expiration_date
                    and latest_record.expiration_date < timezone.localdate()
                ),
                'form': form,
                'open_edit_modal': True,
            },
        )
    latest_record = latest_vaccination_record(dog)
    is_vaccine_expired = bool(
        latest_record
        and latest_record.expiration_date
        and latest_record.expiration_date < timezone.localdate()
    )
    return render(
        request,
        'dogs/owner_detail.html',
        {
            'dog': dog,
            'latest_vaccination': latest_record,
            'is_vaccine_expired': is_vaccine_expired,
            'form': form,
            'open_edit_modal': True,
        },
    )


@login_required
@verified_required
def request_vaccination_schedule(request, pk: int):
    dog = get_object_or_404(
        Dog,
        pk=pk,
        owner=request.user,
        capture_datetime__isnull=True,
        surrender_datetime__isnull=True,
        registration_approval_status=Dog.RegistrationApprovalStatus.APPROVED,
    )
    if request.method != 'POST':
        messages.info(request, 'Use the button on the profile to request a new vaccination schedule.')
        return redirect('dogs_owner_detail', pk=dog.pk)
    latest_record = latest_vaccination_record(dog)
    if (
        not latest_record
        or not latest_record.expiration_date
        or latest_record.expiration_date >= timezone.localdate()
    ):
        messages.warning(
            request,
            'A new schedule can be requested once the vaccine is expired.',
        )
        return redirect('dogs_owner_detail', pk=dog.pk)
    dog.vaccination_status = Dog.VaccinationStatus.UNVACCINATED
    dog.vaccination_request = True
    dog.vaccination_schedule = None
    dog.vaccination_proof = ''
    dog.registration_approval_status = Dog.RegistrationApprovalStatus.PENDING
    dog.registration_reviewed_at = None
    dog.registration_reviewed_by = None
    dog.save(
        update_fields=[
            'vaccination_status',
            'vaccination_request',
            'vaccination_schedule',
            'vaccination_proof',
            'registration_approval_status',
            'registration_reviewed_at',
            'registration_reviewed_by',
        ]
    )
    notify_vaccination_staff(
        'New vaccination schedule request',
        (
            f'Owner {request.user.email} requested a new vaccination schedule for '
            f'"{dog.name or "Unnamed Dog"}" after vaccine expiry.'
        ),
    )
    messages.success(
        request,
        'Vaccination schedule request submitted. This dog will reappear after staff approval.',
    )
    return redirect('profile')
