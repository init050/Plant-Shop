from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.views.generic import View
from django.http import JsonResponse
from .forms import (
    UserRegistrationForm, CustomAuthenticationForm, CustomPasswordChangeForm,
    CustomPasswordResetForm, CustomSetPasswordForm, UserProfileForm
)
from .services import UserService, ProfileService, SecurityService, SocialAuthService
import json


# Create your views here.

class RegisterView(View):
    def get(self, request):
        form = UserRegistrationForm()
        return render(request, 'account_module/register.html', {'form': form})

    def post(self, request):
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = UserService.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password1'],
                phone_number=form.cleaned_data.get('phone_number')
            )
            UserService.send_verification_email(user)
            messages.success(request, _('Registration successful. Please check your email for verification.'))
            return redirect('login')
        return render(request, 'account_module/register.html', {'form': form})

class LoginView(View):
    def get(self, request):
        form = CustomAuthenticationForm()
        return render(request, 'account_module/login.html', {'form': form})

    def post(self, request):
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                SecurityService.update_last_login_ip(user, request.META.get('REMOTE_ADDR'))
                messages.success(request, _('Login successful.'))
                return redirect('profile')
        return render(request, 'account_module/login.html', {'form': form})

class LogoutView(View):
    def get(self, request):
        logout(request)
        messages.success(request, _('Logout successful.'))
        return redirect('login')

class ProfileView(View):
    @login_required
    def get(self, request):
        form = UserProfileForm(instance=request.user)
        return render(request, 'account_module/profile.html', {'form': form})

    @login_required
    def post(self, request):
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            ProfileService.update_profile(request.user, form.cleaned_data)
            messages.success(request, _('Profile updated successfully.'))
            return redirect('profile')
        return render(request, 'account_module/profile.html', {'form': form})

class PasswordChangeView(View):
    @login_required
    def get(self, request):
        form = CustomPasswordChangeForm(request.user)
        return render(request, 'account_module/password_change.html', {'form': form})

    @login_required
    def post(self, request):
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _('Password changed successfully.'))
            return redirect('profile')
        return render(request, 'account_module/password_change.html', {'form': form})

class PasswordResetView(View):
    def get(self, request):
        form = CustomPasswordResetForm()
        return render(request, 'account_module/password_reset.html', {'form': form})

    def post(self, request):
        form = CustomPasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                UserService.send_password_reset_email(user)
                messages.success(request, _('Password reset email sent.'))
                return redirect('login')
            except User.DoesNotExist:
                messages.error(request, _('No user found with this email address.'))
        return render(request, 'account_module/password_reset.html', {'form': form})

class PasswordResetConfirmView(View):
    def get(self, request, token):
        user = SecurityService.validate_password_reset_token(token)
        if user:
            form = CustomSetPasswordForm(user)
            return render(request, 'account_module/password_reset_confirm.html', {'form': form})
        messages.error(request, _('Invalid or expired password reset link.'))
        return redirect('password_reset')

    def post(self, request, token):
        user = SecurityService.validate_password_reset_token(token)
        if user:
            form = CustomSetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                user.clear_password_reset_token()
                messages.success(request, _('Password reset successful.'))
                return redirect('login')
            return render(request, 'account_module/password_reset_confirm.html', {'form': form})
        messages.error(request, _('Invalid or expired password reset link.'))
        return redirect('password_reset')

class EmailVerificationView(View):
    def get(self, request, code):
        try:
            user = User.objects.get(email_active_code=code)
            if UserService.verify_email(user, code):
                messages.success(request, _('Email verified successfully.'))
                return redirect('login')
            messages.error(request, _('Invalid verification code.'))
        except User.DoesNotExist:
            messages.error(request, _('Invalid verification code.'))
        return redirect('login')

class SocialLinksView(View):
    @login_required
    def get(self, request):
        social_links = SocialAuthService.get_social_links(request.user)
        return JsonResponse({'social_links': social_links})

    @login_required
    def post(self, request):
        try:
            social_links = json.loads(request.body)
            SocialAuthService.update_social_links(request.user, social_links)
            return JsonResponse({'status': 'success'})
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': _('Invalid JSON format')}, status=400)
