from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser, EmailOTP, FaceVerification, UserProfile


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    extra = 0


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    inlines = [UserProfileInline]
    fieldsets = UserAdmin.fieldsets + (
        (
            'Verification',
            {'fields': ('role', 'email_verified', 'is_verified', 'legal_consent')},
        ),
    )
    list_display = ('username', 'email', 'role', 'email_verified', 'is_verified', 'is_active')
    list_filter = ('role', 'email_verified', 'is_verified', 'is_active')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'offense_count', 'status_badge')


@admin.register(EmailOTP)
class EmailOTPAdmin(admin.ModelAdmin):
    list_display = ('user', 'purpose', 'is_used', 'expires_at', 'created_at')
    list_filter = ('purpose', 'is_used')


@admin.register(FaceVerification)
class FaceVerificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'status', 'reviewed_by', 'reviewed_at')
    list_filter = ('status',)
