from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

from core.models import TimeStampedModel


class CustomUser(AbstractUser):
    class Roles(models.TextChoices):
        ADMIN = 'ADMIN', 'Admin'
        STAFF = 'STAFF', 'Staff'
        OWNER = 'OWNER', 'Regular User (Owner)'

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=Roles.choices, default=Roles.OWNER)
    email_verified = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    legal_consent = models.BooleanField(default=False)
    legal_consented_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.username} ({self.get_role_display()})"


class UserProfile(models.Model):
    class StatusBadge(models.TextChoices):
        GREEN = 'GREEN', 'Green'
        ORANGE = 'ORANGE', 'Orange'
        RED = 'RED', 'Red'

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')
    offense_count = models.PositiveIntegerField(default=0)
    status_badge = models.CharField(max_length=10, choices=StatusBadge.choices, default=StatusBadge.GREEN)
    full_name = models.CharField(max_length=150, blank=True)
    address = models.CharField(max_length=255, blank=True)
    age = models.PositiveIntegerField(null=True, blank=True)
    birthday = models.DateField(null=True, blank=True)

    def __str__(self) -> str:
        return f"Profile: {self.user.username}"


class EmailOTP(TimeStampedModel):
    class Purpose(models.TextChoices):
        REGISTRATION = 'REGISTRATION', 'Registration'
        LOGIN = 'LOGIN', 'Login'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='email_otps')
    purpose = models.CharField(max_length=20, choices=Purpose.choices, default=Purpose.REGISTRATION)
    code_hash = models.CharField(max_length=128)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    def is_expired(self) -> bool:
        return timezone.now() >= self.expires_at

    def __str__(self) -> str:
        return f"EmailOTP for {self.user.username} ({self.purpose})"


class FaceVerification(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='face_verification'
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='face_verification_reviews',
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    photo = models.FileField(upload_to='face_verifications/', blank=True)

    def __str__(self) -> str:
        return f"FaceVerification {self.user.username} - {self.get_status_display()}"
