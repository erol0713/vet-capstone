from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect

from .models import CustomUser


def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            if request.user.role not in roles:
                messages.error(request, 'You do not have permission to access this page.')
                return redirect('dashboard')
            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator


def verified_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.role in (CustomUser.Roles.ADMIN, CustomUser.Roles.STAFF):
            return view_func(request, *args, **kwargs)
        if not request.user.email_verified or not request.user.is_verified:
            messages.warning(request, 'Complete verification to access this feature.')
            return redirect('verification_status')
        return view_func(request, *args, **kwargs)

    return _wrapped
