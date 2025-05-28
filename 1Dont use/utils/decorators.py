from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from functools import wraps

def email_verification_required(view_func):
    """Decorator to ensure user has verified their email"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_email_verified:
            if request.is_ajax():
                return JsonResponse({
                    'error': _('Email verification required'),
                    'redirect': 'verify_email'
                }, status=403)
            return redirect('verify_email')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def profile_owner_required(view_func):
    """Decorator to ensure user can only access their own profile"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.id != kwargs.get('user_id'):
            raise PermissionDenied(_('You do not have permission to access this profile'))
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def social_auth_required(view_func):
    """Decorator to ensure user has social authentication enabled"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.social_links:
            if request.is_ajax():
                return JsonResponse({
                    'error': _('Social authentication required'),
                    'redirect': 'profile'
                }, status=403)
            return redirect('profile')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def ajax_required(view_func):
    """Decorator to ensure the request is AJAX"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.is_ajax():
            return JsonResponse({'error': _('AJAX request required')}, status=400)
        return view_func(request, *args, **kwargs)
    return _wrapped_view 