from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CustomUser, FaceVerification, UserProfile


@receiver(post_save, sender=CustomUser)
def create_profile_for_user(sender, instance: CustomUser, created: bool, **kwargs) -> None:
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=FaceVerification)
def sync_user_verification(sender, instance: FaceVerification, **kwargs) -> None:
    if instance.status == FaceVerification.Status.APPROVED:
        CustomUser.objects.filter(id=instance.user_id).update(is_verified=True)


@receiver(post_save, sender=CustomUser)
def sync_roles_for_admin(sender, instance: CustomUser, **kwargs) -> None:
    if instance.is_superuser and instance.role != CustomUser.Roles.ADMIN:
        CustomUser.objects.filter(id=instance.id).update(
            role=CustomUser.Roles.ADMIN, email_verified=True, is_verified=True
        )
        return
    if instance.is_staff and instance.role not in (CustomUser.Roles.ADMIN, CustomUser.Roles.STAFF):
        CustomUser.objects.filter(id=instance.id).update(
            role=CustomUser.Roles.STAFF, email_verified=True, is_verified=True
        )
