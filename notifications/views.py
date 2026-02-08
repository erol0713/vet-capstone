from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme

from .models import Notification


@login_required
def inbox(request):
    items = Notification.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'notifications/inbox.html', {'items': items})


@login_required
def mark_read(request, pk: int):
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.is_read = True
    notification.save(update_fields=['is_read'])
    target = (notification.action_url or '').strip()
    if target and url_has_allowed_host_and_scheme(
        url=target,
        allowed_hosts={request.get_host()},
    ):
        return redirect(target)
    return redirect('notifications_inbox')


@login_required
def mark_all_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return redirect('notifications_inbox')
