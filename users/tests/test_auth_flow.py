from datetime import timedelta

from django.utils import timezone

from users.models import CustomUser, EmailOTP
from users.services import create_email_otp, verify_email_otp


def test_registration_creates_user(client):
    response = client.post(
        '/accounts/register/',
        {
            'email': 'user@example.com',
            'barangay': 'Poblacion',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
            'legal_consent': True,
        },
        follow=True,
    )

    assert response.status_code == 200
    assert CustomUser.objects.filter(email='user@example.com').exists()


def test_otp_verification_success():
    user = CustomUser.objects.create_user(
        username='otp@example.com',
        email='otp@example.com',
        password='StrongPass123!',
        legal_consent=True,
        legal_consented_at=timezone.now(),
    )
    code = create_email_otp(user)
    assert verify_email_otp(user, code) is True


def test_otp_verification_expired():
    user = CustomUser.objects.create_user(
        username='expired@example.com',
        email='expired@example.com',
        password='StrongPass123!',
        legal_consent=True,
        legal_consented_at=timezone.now(),
    )
    code = create_email_otp(user)
    otp = EmailOTP.objects.filter(user=user).latest('created_at')
    otp.expires_at = timezone.now() - timedelta(minutes=1)
    otp.save(update_fields=['expires_at'])

    assert verify_email_otp(user, code) is False
