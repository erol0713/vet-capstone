import base64

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.db.models import Prefetch, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import FaceVerificationSubmitForm, LoginForm, OTPVerifyForm, ProfileInfoForm, RegistrationForm
from adoption.models import AdoptionReservation, ReclaimRequest
from dogs.models import Dog
from reports.models import Report
from vaccinations.models import VaccinationRecord
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
    report_count = Report.objects.filter(reported_by=request.user).count()
    adoption_count = AdoptionReservation.objects.filter(requester=request.user).count()
    reclaim_count = ReclaimRequest.objects.filter(owner=request.user).count()
    context = {
        'report_count': report_count,
        'adoption_count': adoption_count,
        'reclaim_count': reclaim_count,
    }
    return render(request, 'users/dashboard.html', context)


@login_required
def profile(request):
    profile_obj = request.user.profile
    registered_dogs = (
        request.user.dogs.filter(
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
    )
    for dog in registered_dogs:
        dog.latest_vaccination = (
            dog.vaccination_records_cache[0] if dog.vaccination_records_cache else None
        )
    form = ProfileInfoForm(request.POST or None, request.FILES or None, instance=profile_obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Profile updated.')
        return redirect('profile')
    return render(request, 'users/profile.html', {'form': form, 'registered_dogs': registered_dogs})


@login_required
@role_required('ADMIN', 'STAFF')
def verification_detail(request, pk: int):
    record = get_object_or_404(FaceVerification, pk=pk)
    return render(request, 'users/verification_detail.html', {'record': record})


@login_required
@role_required('ADMIN', 'STAFF')
def admin_user_management(request):
    users = (
        CustomUser.objects.select_related('profile', 'face_verification')
        .order_by('-date_joined')
        .all()
    )
    query = request.GET.get('q', '').strip()
    role = request.GET.get('role', '').strip()
    verification = request.GET.get('verification', '').strip()

    if query:
        users = users.filter(
            Q(username__icontains=query)
            | Q(email__icontains=query)
            | Q(profile__full_name__icontains=query)
        )
    if role in dict(CustomUser.Roles.choices):
        users = users.filter(role=role)
    if verification == 'email_verified':
        users = users.filter(email_verified=True)
    elif verification == 'email_unverified':
        users = users.filter(email_verified=False)
    elif verification == 'face_pending':
        users = users.filter(face_verification__status=FaceVerification.Status.PENDING)
    elif verification == 'face_approved':
        users = users.filter(face_verification__status=FaceVerification.Status.APPROVED)
    elif verification == 'face_rejected':
        users = users.filter(face_verification__status=FaceVerification.Status.REJECTED)
    elif verification == 'fully_verified':
        users = users.filter(email_verified=True, is_verified=True)
    elif verification == 'not_verified':
        users = users.filter(is_verified=False)

    summary = {
        'total': CustomUser.objects.count(),
        'email_verified': CustomUser.objects.filter(email_verified=True).count(),
        'face_pending': FaceVerification.objects.filter(status=FaceVerification.Status.PENDING).count(),
        'fully_verified': CustomUser.objects.filter(email_verified=True, is_verified=True).count(),
    }

    context = {
        'users': users,
        'query': query,
        'role_filter': role,
        'verification_filter': verification,
        'summary': summary,
        'roles': CustomUser.Roles,
    }
    return render(request, 'users/admin_user_management.html', context)


@login_required
@role_required('ADMIN', 'STAFF')
@require_POST
def admin_user_management_action(request):
    action = request.POST.get('action', '').strip()
    user_id = request.POST.get('user_id', '').strip()
    next_url = request.POST.get('next', '')
    target_user = get_object_or_404(CustomUser, pk=user_id)

    if action == 'mark_email_verified':
        target_user.email_verified = True
        target_user.save(update_fields=['email_verified'])
        messages.success(request, 'Email verification updated.')
    elif action == 'mark_email_unverified':
        target_user.email_verified = False
        target_user.save(update_fields=['email_verified'])
        messages.success(request, 'Email verification updated.')
    elif action == 'mark_verified':
        target_user.is_verified = True
        target_user.save(update_fields=['is_verified'])
        messages.success(request, 'User verification updated.')
    elif action == 'mark_unverified':
        target_user.is_verified = False
        target_user.save(update_fields=['is_verified'])
        messages.success(request, 'User verification updated.')
    elif action in ('approve_face', 'reject_face'):
        record = FaceVerification.objects.filter(user=target_user).first()
        if not record:
            messages.error(request, 'No face verification submission found.')
        else:
            status = (
                FaceVerification.Status.APPROVED
                if action == 'approve_face'
                else FaceVerification.Status.REJECTED
            )
            record.status = status
            record.reviewed_by = request.user
            record.reviewed_at = timezone.now()
            record.save(update_fields=['status', 'reviewed_by', 'reviewed_at'])
            target_user.is_verified = action == 'approve_face'
            target_user.save(update_fields=['is_verified'])
            messages.success(request, 'Face verification updated.')
    else:
        messages.error(request, 'Invalid action.')

    if next_url and url_has_allowed_host_and_scheme(next_url, {request.get_host()}):
        return redirect(next_url)
    return redirect('admin_user_management')
