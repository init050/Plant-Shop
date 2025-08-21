from django.http import HttpResponse
from django.views import generic
import logging
from django.contrib.auth import get_user_model
from .models import User
from .forms.registration import UserRegistrationForm, UserProfileForm
from django.views.generic.edit import FormView
from .forms.auth import(
    CustomAuthenticationForm, CustomPasswordChangeForm,
    CustomPasswordResetForm, CustomSetPasswordForm
)
from .services.email_verification import EmailVerificationService
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
    success_url = reverse_lazy('home_page')

    def form_valid(self, form):
        # We need to save the user first before we can send the verification email.
        # The `commit=False` allows us to get the user object without saving it to the database yet.
        user = form.save(commit=False)
        user.is_active = False # The user should not be active until they verify their email.
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

    def form_valid(self, form):
        # After the form is validated and the user is retrieved, we can add custom logic.
        user = form.get_user()

        # It's important to check for email verification here to provide immediate feedback
        # to the user, rather than letting them access parts of the site they shouldn't.
        if not user.is_email_verified:
            messages.warning(self.request, _('Your email is not verified. Please check your inbox.'))
        
        login(self.request, user)
        
        # Logging the last login IP is a good security practice.
        # We've moved the IP retrieval logic to a dedicated utility for better code organization.
        user.last_login_ip = get_client_ip(self.request)
        user.save(update_fields=['last_login_ip'])

        return super().form_valid(form)



class UserProfileView(LoginRequiredMixin, BaseViewMixin, generic.UpdateView):
    model = User
    form_class = UserProfileForm
    template_name = 'account_module/profile.html'
    success_url = reverse_lazy('account_module:profile')

    def get_object(self, queryset=None):
        # This ensures that the user can only edit their own profile.
        return self.request.user

    def form_valid(self, form):
        # By letting the form handle the save, we keep the view cleaner.
        # The UserProfileForm is designed to only allow certain fields to be edited,
        # and the ModelForm's save() method respects this.
        messages.success(self.request, _('Profile updated successfully.'))
        return super().form_valid(form)    


class PasswordChangeView(LoginRequiredMixin, FormView):
    form_class = CustomPasswordChangeForm
    template_name = 'account_module/change_password.html'
    success_url = reverse_lazy('home_page')

    def get_object(self, queryset = None):
        return self.request.user
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user 
        return kwargs
    

    def form_valid(self, form):
        form.save()
        messages.success(self.request, _('Password changed successfully'))
        return super().form_valid(form)
    

class CustomPasswordResetView(PasswordResetView):
    # This view initiates the password reset process. By inheriting from PasswordResetView,
    # we get the logic for sending the reset email for free. We just need to
    # point it to our custom form and templates.
    form_class = CustomPasswordResetForm
    template_name = 'account_module/password_reset_form.html'
    email_template_name = 'account_module/password_reset_email.html'
    subject_template_name = 'account_module/password_reset_subject.txt'
    success_url = reverse_lazy('account_module:password_reset_done')

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


class EmailVerificationView(generic.View):
    # This view is now a simple handler for the verification link.
    # It's lean because all the complex logic has been moved to the EmailVerificationService.
    # This separation of concerns makes the code easier to read, test, and maintain.
    def get(self, request, token):
        success, message = EmailVerificationService.verify(token)
        if success:
            messages.success(request, message)
        else:
            messages.error(request, message)
        return redirect('account_module:login')