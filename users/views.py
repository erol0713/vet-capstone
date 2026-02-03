import base64

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import FaceVerificationSubmitForm, LoginForm, OTPVerifyForm, ProfileInfoForm, RegistrationForm
from .models import CustomUser, FaceVerification
from .services import create_email_otp, verify_email_otp
from users.decorators import role_required


def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    form = RegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        email = form.cleaned_data['email']
        username = form.cleaned_data['username']
        password = form.cleaned_data['password1']

        user = CustomUser.objects.create_user(
            username=username,
            email=email,
            password=password,
            legal_consent=form.cleaned_data.get('legal_consent', False),
            legal_consented_at=timezone.now(),
        )
        request.session['pending_user_id'] = user.id
        code = create_email_otp(user)
        messages.success(request, f'OTP sent to {email}. Dev code: {code}')
        return redirect('verify_email')

    return render(request, 'users/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)
        return redirect('dashboard')

    return render(request, 'users/login.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    return redirect('home')


def verify_email(request):
    user_id = request.session.get('pending_user_id')
    if not user_id:
        messages.error(request, 'No pending verification.')
        return redirect('register')

    user = CustomUser.objects.filter(id=user_id).first()
    if not user:
        messages.error(request, 'User not found.')
        return redirect('register')

    form = OTPVerifyForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        code = form.cleaned_data['code']
        if verify_email_otp(user, code):
            user.email_verified = True
            user.save(update_fields=['email_verified'])
            login(request, user)
            messages.success(request, 'Email verified.')
            return redirect('verification_status')

        messages.error(request, 'Invalid or expired code.')

    return render(request, 'users/verify_email.html', {'form': form, 'user': user})


@login_required
def verification_status(request):
    return render(request, 'users/verification_status.html')


@login_required
def submit_face_verification(request):
    profile = request.user.profile
    required_fields = [profile.full_name, profile.address, profile.age, profile.birthday]
    if not all(required_fields):
        messages.warning(request, 'Complete your profile information before face verification.')
        return redirect('profile')
    form = FaceVerificationSubmitForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        if request.POST.get('liveness_passed') != '1':
            messages.error(request, 'Liveness check not completed.')
            return redirect('face_verification')
        record, _ = FaceVerification.objects.get_or_create(user=request.user)
        record.status = FaceVerification.Status.PENDING
        snapshot = request.POST.get('snapshot')
        if snapshot and snapshot.startswith('data:image'):
            header, data = snapshot.split(',', 1)
            ext = header.split('/')[1].split(';')[0]
            file_data = ContentFile(base64.b64decode(data), name=f'face_{request.user.id}.{ext}')
            record.photo = file_data
        record.save()
        messages.success(request, 'Face verification submitted for review.')
        return redirect('verification_status')

    return render(request, 'users/face_verification.html', {'form': form})


@login_required
def dashboard(request):
    return render(request, 'users/dashboard.html')


@login_required
def profile(request):
    profile_obj = request.user.profile
    registered_dogs = request.user.dogs.filter(
        capture_datetime__isnull=True,
        surrender_datetime__isnull=True,
    )
    form = ProfileInfoForm(request.POST or None, instance=profile_obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Profile updated.')
        return redirect('profile')
    return render(request, 'users/profile.html', {'form': form, 'registered_dogs': registered_dogs})


@login_required
@role_required('ADMIN', 'STAFF')
def verification_queue(request):
    pending = FaceVerification.objects.select_related('user').order_by('-created_at')
    return render(request, 'users/verification_queue.html', {'pending': pending})


@login_required
@role_required('ADMIN', 'STAFF')
def verification_update(request, pk: int, status: str):
    record = get_object_or_404(FaceVerification, pk=pk)
    if status not in (FaceVerification.Status.APPROVED, FaceVerification.Status.REJECTED):
        messages.error(request, 'Invalid status.')
        return redirect('verification_queue')
    record.status = status
    record.reviewed_by = request.user
    record.reviewed_at = timezone.now()
    record.save(update_fields=['status', 'reviewed_by', 'reviewed_at'])
    messages.success(request, f'User verification marked as {record.get_status_display()}.')
    return redirect('verification_queue')


@login_required
@role_required('ADMIN', 'STAFF')
def verification_detail(request, pk: int):
    record = get_object_or_404(FaceVerification, pk=pk)
    return render(request, 'users/verification_detail.html', {'record': record})
