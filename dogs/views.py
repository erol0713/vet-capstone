from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from users.decorators import role_required, verified_required

from .forms import DogForm, UserDogRegistrationForm
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
    return render(
        request,
        'dogs/public_detail.html',
        {'dog': dog, 'can_reclaim': can_reclaim, 'can_adopt': can_adopt},
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
def create_dog(request):
    form = DogForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        dog = form.save(commit=False)
        apply_intake_status(dog)
        dog.save()
        messages.success(request, f'Dog #{dog.pk} created.')
        return redirect('dogs_manage_list')
    return render(request, 'dogs/form.html', {'form': form, 'title': 'Create Dog', 'dog': None})


@login_required
@role_required('ADMIN', 'STAFF')
def edit_dog(request, pk: int):
    dog = get_object_or_404(Dog, pk=pk)
    form = DogForm(request.POST or None, request.FILES or None, instance=dog)
    if request.method == 'POST' and form.is_valid():
        dog = form.save(commit=False)
        apply_intake_status(dog)
        dog.save()
        messages.success(request, f'Dog #{dog.pk} updated.')
        return redirect('dogs_manage_list')
    return render(
        request,
        'dogs/form.html',
        {'form': form, 'title': f'Edit Dog #{dog.pk}', 'dog': dog},
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
