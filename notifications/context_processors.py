from .models import Notification


def unread_notifications(request):
    if not request.user.is_authenticated:
        return {'unread_notifications': 0, 'nav_notifications': []}

    items = Notification.objects.filter(user=request.user).order_by('-created_at')
    count = items.filter(is_read=False).count()
    return {
        'unread_notifications': count,
        'nav_notifications': items[:5],
    }
