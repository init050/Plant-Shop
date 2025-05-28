from django.views import generic
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404, render
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from django.db.models import Q
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
import logging
from typing import Any, Dict
import json

from .forms.auth import LoginForm, PasswordChangeForm
from .forms.registration import UserRegistrationForm, UserProfileUpdateForm
from .models import User
from .services.email_verification import EmailVerificationService



#! do not use this viewset------------------------!!!!



logger = logging.getLogger(__name__)

User = get_user_model()

class BaseViewMixin:
    """Base mixin for common view functionality"""
    
    def get_context_data(self, **kwargs):   
        context = super().get_context_data(**kwargs)
        context['current_page'] = self.request.resolver_match.url_name
        return context

    def handle_exception(self, exc):
        logger.error(f"Error in {self.__class__.__name__}: {str(exc)}")
        return super().handle_exception(exc)

class UserRegistrationView(generic.CreateView):
    """Advanced user registration view with email verification"""
    model = User
    form_class = UserRegistrationForm
    template_name = 'account/registration.html'
    success_url = reverse_lazy('account:login')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        user = form.save()
        
        # Send verification email using the service
        if EmailVerificationService.send_verification_email(user):
            messages.success(
                self.request,
                _('Registration successful. Please check your email for verification.')
            )
        else:
            messages.warning(
                self.request,
                _('Registration successful, but we could not send the verification email. Please try again later.')
            )
        return response

    def form_invalid(self, form):
        messages.error(
            self.request,
            _('Registration failed. Please check the form and try again.')
        )
        return super().form_invalid(form)

class CustomLoginView(generic.View):
    """Advanced login view with security features"""
    template_name = 'account/login.html'
    form_class = LoginForm

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('home')
        return self.render_form()

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            # Update last login IP
            user.last_login_ip = self.get_client_ip(request)
            user.save(update_fields=['last_login_ip'])
            
            next_url = request.GET.get('next', 'home')
            return redirect(next_url)
        
        return self.render_form(form)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def render_form(self, form=None):
        if form is None:
            form = self.form_class()
        return render(self.request, self.template_name, {'form': form})

class UserProfileView(LoginRequiredMixin, BaseViewMixin, generic.UpdateView):
    """Advanced user profile management view"""
    model = User
    form_class = UserProfileUpdateForm
    template_name = 'account/profile.html'
    success_url = reverse_lazy('account:profile')

    def get_object(self, queryset=None):
        return self.request.user

    @method_decorator(cache_page(60 * 15))  # Cache for 15 minutes
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, _('Profile updated successfully'))
        return super().form_valid(form)

class PasswordChangeView(LoginRequiredMixin, generic.UpdateView):
    """Secure password change view"""
    form_class = PasswordChangeForm
    template_name = 'account/password_change.html'
    success_url = reverse_lazy('account:profile')

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        form.save()
        messages.success(self.request, _('Password changed successfully'))
        return super().form_valid(form)

# API Views
class UserViewSet(viewsets.ModelViewSet): #! do not use this viewset------------------------
    """REST API viewset for user management"""
    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(id=self.request.user.id)
        return queryset

    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def logout(self, request):
        try:
            refresh_token = request.data["refresh_token"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)



class CustomPasswordResetView(PasswordResetView):
    """Custom password reset view with enhanced security"""
    template_name = 'account/password_reset.html'
    email_template_name = 'account/password_reset_email.html'
    success_url = reverse_lazy('account:password_reset_done')

    def form_valid(self, form):
        email = form.cleaned_data['email']
        try:
            user = User.objects.get(email=email)
            user.generate_password_reset_token()
            messages.success(
                self.request,
                _('Password reset instructions have been sent to your email.')
            )
        except User.DoesNotExist:
            messages.success(
                self.request,
                _('If an account exists with this email, you will receive password reset instructions.')
            )
        return super().form_valid(form)
    
    

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    """Custom password reset confirmation view"""
    template_name = 'account/password_reset_confirm.html'
    success_url = reverse_lazy('account:password_reset_complete')

    def form_valid(self, form):
        response = super().form_valid(form)
        user = form.user
        user.clear_password_reset_token()
        messages.success(self.request, _('Password has been reset successfully'))
        return response
    

    
class EmailVerificationView(generic.View):
    """Email verification view"""
    def get(self, request, code):
        user = get_object_or_404(User, email_active_code=code)
        if EmailVerificationService.verify_email(user, code):
            messages.success(request, _('Email verified successfully'))
            return redirect('account:login')
        messages.error(request, _('Invalid verification code'))
        return redirect('account:login')
    

