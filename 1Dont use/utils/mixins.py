from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _

class AjaxRequiredMixin:
    """Mixin to ensure the request is AJAX"""
    def dispatch(self, request, *args, **kwargs):
        if not request.is_ajax():
            return JsonResponse({'error': _('AJAX request required')}, status=400)
        return super().dispatch(request, *args, **kwargs)

class EmailVerificationRequiredMixin(LoginRequiredMixin):
    """Mixin to ensure user has verified their email"""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_email_verified:
            return JsonResponse({
                'error': _('Email verification required'),
                'redirect': 'verify_email'
            }, status=403)
        return super().dispatch(request, *args, **kwargs)

class ProfileOwnerRequiredMixin(LoginRequiredMixin):
    """Mixin to ensure user can only access their own profile"""
    def dispatch(self, request, *args, **kwargs):
        if request.user.id != kwargs.get('user_id'):
            raise PermissionDenied(_('You do not have permission to access this profile'))
        return super().dispatch(request, *args, **kwargs)

class SocialAuthRequiredMixin(LoginRequiredMixin):
    """Mixin to ensure user has social authentication enabled"""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.social_links:
            return JsonResponse({
                'error': _('Social authentication required'),
                'redirect': 'profile'
            }, status=403)
        return super().dispatch(request, *args, **kwargs) 