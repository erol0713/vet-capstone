import secrets
from datetime import timedelta

from django.contrib.auth.hashers import check_password, make_password
from django.utils import timezone

from .models import EmailOTP


def create_email_otp(user, purpose=EmailOTP.Purpose.REGISTRATION, minutes_valid=10) -> str:
    code = f"{secrets.randbelow(1000000):06d}"
    expires_at = timezone.now() + timedelta(minutes=minutes_valid)
    EmailOTP.objects.create(
        user=user,
        purpose=purpose,
        code_hash=make_password(code),
        expires_at=expires_at,
    )
    return code


def verify_email_otp(user, code, purpose=EmailOTP.Purpose.REGISTRATION) -> bool:
    otp = (
        EmailOTP.objects.filter(user=user, purpose=purpose, is_used=False)
        .order_by('-created_at')
        .first()
    )
    if not otp or otp.is_expired():
        return False
    if not check_password(code, otp.code_hash):
        return False
    otp.is_used = True
    otp.save(update_fields=['is_used'])
    return True
