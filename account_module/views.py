from django.http import HttpResponse
from django.views import generic
import logging
from django.contrib.auth import get_user_model
from .models import User
from .forms.registration import UserRegistrationForm, UserProfileForm
from .forms.email_change import EmailChangeForm, OldEmailVerificationForm
from django.views.generic.edit import FormView
from .forms.auth import(
    CustomAuthenticationForm, CustomPasswordChangeForm,
    CustomPasswordResetForm, CustomSetPasswordForm
)
from .services.email_verification import EmailVerificationService
from .services.email_change_service import EmailChangeService
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.shortcuts import redirect, render
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.contrib.auth.views import (
    PasswordResetView, PasswordResetConfirmView,
    PasswordResetDoneView, PasswordResetCompleteView
)
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)
user = get_user_model()

class BaseViewMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_page'] = self.request.resolver_match.url_name
        return context
    
    def handle_exception(self, exc):
        logger.error(f'Error in {self.__class__.__name__}: {str(exc)}')
        return super().handle_exception(exc)
    

class UserRegistrationView(generic.CreateView):
    model = User
    form_class = UserRegistrationForm
    template_name = 'account_module/register.html'
    success_url = reverse_lazy('account_module:email_verification')

    def form_valid(self, form):
        # We need to save the user first before we can send the verification email.
        # The `commit=False` allows us to get the user object without saving it to the database yet.
        user = form.save(commit=False)
        user.is_active = False # The user should not be active until they verify their email.
        user.is_email_verified = False
        user.save()

        # We pass the request object to the service so it can build the absolute verification URL.
        if EmailVerificationService.send_verification_email(self.request, user):
            messages.success(
                self.request,
                _('Registration successful. Please check your email for verification.')
            )
        else:
            messages.warning(
                self.request,
                _('Registration successful, but we could not send the verification email. Please try again later.')
            )
        
        self.request.session['pending_verification_user_id'] = user.id
        return redirect(self.success_url)
    
    def form_invalid(self, form):
        messages.error(
            self.request,
            _('Registration failed. Please check the form and try again.')
        )
        return super().form_invalid(form)


from django.contrib.auth.views import LoginView
from .utils.ip_retriever import get_client_ip


class CustomLoginView(LoginView):
    # Inheriting from Django's LoginView provides a robust, well-tested foundation.
    # We only need to customize the form and add our specific post-login logic (like IP logging)
    # instead of rebuilding the entire GET/POST handling from scratch.
    form_class = CustomAuthenticationForm
    template_name = 'account_module/login.html'

    def get_success_url(self):
        next_url = self.request.GET.get('next')
        if next_url:
            return next_url
        return reverse_lazy('home_page')

    def form_valid(self, form):
        # After the form is validated and the user is retrieved, we can add custom logic.
        user = form.get_user()

        # It's important to check for email verification here to provide immediate feedback
        # to the user, rather than letting them access parts of the site they shouldn't.
        if not user.can_login():
            messages.error(
                self.request, 
                _('Your email is not verified. Please check your inbox and verify your email first.')
            )
            self.request.session['pending_verification_user_id'] = user.id
            return redirect('account_module:email_verification')
        
        login(self.request, user)
        
        # Logging the last login IP is a good security practice.
        # We've moved the IP retrieval logic to a dedicated utility for better code organization.
        user.last_login_ip = get_client_ip(self.request)
        user.save(update_fields=['last_login_ip'])

        messages.success(self.request, _('Welcome back!'))
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, _('Invalid email or password.'))
        return super().form_invalid(form)


class UserProfileView(LoginRequiredMixin, BaseViewMixin, generic.UpdateView):
    model = User
    form_class = UserProfileForm
    template_name = 'account_module/profile.html'
    success_url = reverse_lazy('account_module:profile')

    def get_object(self, queryset=None):
        # This ensures that the user can only edit their own profile.
        return self.request.user

    def form_valid(self, form):
        # Only allow avatar changes in profile - email changes go through separate secure flow
        form.save()
        messages.success(self.request, _('Profile updated successfully.'))
        return redirect(self.success_url)


class EmailChangeInitiateView(LoginRequiredMixin, FormView):
    form_class = EmailChangeForm
    template_name = 'account_module/email_change_initiate.html'
    success_url = reverse_lazy('account_module:email_change_verify_old')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        new_email = form.cleaned_data['new_email']
        
        if EmailChangeService.initiate_email_change(self.request, self.request.user, new_email):
            messages.success(
                self.request,
                _('Verification code sent to your current email. Please check your inbox.')
            )
        else:
            messages.error(
                self.request,
                _('Failed to initiate email change. Please try again.')
            )
        
        return super().form_valid(form)


class EmailChangeVerifyOldView(LoginRequiredMixin, FormView):
    form_class = OldEmailVerificationForm
    template_name = 'account_module/email_change_verify_old.html'
    success_url = reverse_lazy('account_module:email_change_verify_new')

    def form_valid(self, form):
        code = form.cleaned_data['verification_code']
        user = self.request.user
        
        success, message = EmailChangeService.verify_old_email(user, code)
        
        if success:
            # Send verification link to new email
            if EmailChangeService.send_new_email_verification(self.request, user):
                messages.success(
                    self.request,
                    _('Old email verified. Verification link sent to your new email address.')
                )
            else:
                messages.error(
                    self.request,
                    _('Old email verified but failed to send verification to new email.')
                )
        else:
            messages.error(self.request, message)
            return self.form_invalid(form)
        
        return super().form_valid(form)


class EmailChangeVerifyNewView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'account_module/email_change_verify_new.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pending_email'] = self.request.user.pending_email
        return context


class PasswordChangeView(LoginRequiredMixin, FormView):
    form_class = CustomPasswordChangeForm
    template_name = 'account_module/change_password.html'
    success_url = reverse_lazy('home_page')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user 
        return kwargs
    

    def form_valid(self, form):
        form.save()
        messages.success(self.request, _('Password changed successfully'))
        return super().form_valid(form)


class EmailVerificationView(generic.TemplateView):
    template_name = 'account_module/email_verification.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        user_id = self.request.session.get('pending_verification_user_id')
        if user_id:
            try:
                user = User.objects.get(id=user_id)
                context['user'] = user
            except User.DoesNotExist:
                context['user'] = None
        
        context['can_resend'] = self._can_resend_email(context.get('user'))
        
        return context
    
    def _can_resend_email(self, user):
        if not user:
            return False
        
        if user.is_email_verified:
            return False
            
        last_attempt = self.request.session.get('last_verification_email_sent')
        if last_attempt:
            last_time = timezone.datetime.fromisoformat(last_attempt)
            if timezone.now() - last_time < timedelta(minutes=2):
                return False
        
        return True
    
    def post(self, request, *args, **kwargs):
        user_id = request.session.get('pending_verification_user_id')
        if not user_id:
            messages.error(request, _('No pending verification found.'))
            return redirect('account_module:login')
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            messages.error(request, _('User not found.'))
            return redirect('account_module:login')
        
        if user.is_email_verified:
            messages.info(request, _('Your email is already verified.'))
            return redirect('account_module:login')
        
        if not self._can_resend_email(user):
            messages.warning(request, _('Please wait before requesting another verification email.'))
            return self.get(request, *args, **kwargs)
        
        target_email = user.pending_email if user.pending_email else user.email
        if EmailVerificationService.send_verification_email(request, user, target_email):
            request.session['last_verification_email_sent'] = timezone.now().isoformat()
            messages.success(request, _('Verification email sent successfully.'))
        else:
            messages.error(request, _('Could not send verification email. Please try again later.'))
        
        return self.get(request, *args, **kwargs)


class EmailVerificationConfirmView(generic.View):
    # This view is now a simple handler for the verification link.
    # It's lean because all the complex logic has been moved to the EmailVerificationService.
    # This separation of concerns makes the code easier to read, test, and maintain.
    def get(self, request, token):
        success, message = EmailVerificationService.verify(token)
        
        if success:
            # Check if this is part of email change process
            user = request.user if request.user.is_authenticated else None
            if user and user.old_email_verified and user.pending_email:
                EmailChangeService.complete_email_change(user)
                messages.success(request, _('Email change completed successfully.'))
                return redirect('account_module:profile')
            
            messages.success(request, message)
            if 'pending_verification_user_id' in request.session:
                del request.session['pending_verification_user_id']
            if 'last_verification_email_sent' in request.session:
                del request.session['last_verification_email_sent']
            return redirect('account_module:login')
        else:
            messages.error(request, message)
            return redirect('account_module:email_verification')


class CustomPasswordResetView(PasswordResetView):
    form_class = CustomPasswordResetForm
    template_name = 'account_module/password_reset_form.html'
    email_template_name = 'account_module/password_reset_email.txt'  
    subject_template_name = 'account_module/password_reset_subject.txt'
    success_url = reverse_lazy('account_module:password_reset_done')

    def form_valid(self, form):
        messages.success(
            self.request,
            _('If an account exists with this email, you will receive password reset instructions.')
        )
        return super().form_valid(form)

    def form_valid(self, form):
        messages.success(
            self.request,
            _('If an account exists with this email, you will receive password reset instructions.')
        )
        return super().form_valid(form)


class CustomPasswordResetDoneView(PasswordResetDoneView):
    # This view is shown after the user has been emailed a link.
    # It just needs to render a template confirming that the email has been sent.
    template_name = 'account_module/password_reset_done.html'


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    # This view is where the user actually sets their new password after clicking the link.
    # We provide our custom form for setting the password and a success URL.
    form_class = CustomSetPasswordForm
    template_name = 'account_module/password_reset_confirm.html'
    success_url = reverse_lazy('account_module:password_reset_complete')

    def form_valid(self, form):
        messages.success(
            self.request,
            _('Your password has been reset successfully.')
        )
        return super().form_valid(form)


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    # This is the final step, a page that confirms the password has been successfully changed.
    template_name = 'account_module/password_reset_complete.html'