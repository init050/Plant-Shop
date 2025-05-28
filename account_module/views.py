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
from .services.email_verification import EmailVerificationService


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
        response = super().form_valid(form)
        user = form.save()

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
    template_name = 'account_module/login.html'
    form_class = CustomAuthenticationForm


    def get(self, request):
        if request.user.is_authenticated:
            return redirect('home_page')
        next_url = request.GET.get('next', '')
        return self.render_form(extra_context={'next': next_url})

    def post(self, request):
        form = self.form_class(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            #TODO : Message error : Your mail not verify
            login(request, user)

            user.last_login_ip = self.get_client_ip(request)
            user.save(update_fields=['last_login_ip'])

            next_url = request.POST.get('next') or 'home_page'
            return redirect(next_url)
        
        next_url = request.POST.get('next') or ''
        return self.render_form(form, extra_context={'next': next_url})


    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def render_form(self, form=None, extra_context=None):
        if form is None:
            form = self.form_class()
        context = {'form': form}
        if extra_context:
            context.update(extra_context)
        return render(self.request, self.template_name, context)



class UserProfileView(LoginRequiredMixin, BaseViewMixin, generic.UpdateView):

    model = User
    form_class = UserProfileForm
    template_name = 'account_module/profile.html'
    success_url = reverse_lazy('profile')

    def get_object(self, queryset = None):
        return self.request.user
    
    
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        user = self.get_object()
        user.email = form.cleaned_data['email']
        user.avatar = form.cleaned_data['avatar']
        user.save(update_fields=['email', 'avatar'])
        messages.success(self.request, _('Profile updated successfully'))
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



    form_class = CustomPasswordResetForm
    template_name = ''
    email_template_name = ''
    subject_template_name = ''
    success_url = reverse_lazy('')

    def form_valid(self, form):
        form.save(
            request = self.request,
            use_https = self.request.is_secure(),
            from_email=settings.DEFAULT_FROM_EMAIL, 
            email_template_name = self.email_template_name,
            subject_template_name = self.subject_template_name

        )

        messages.success(
            self.request,
            _('If an account exists with this email, you will receive password reset instructions.')
        )

        return super().form_valid(form)
    

class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'account/password_reset_done.html'


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    form_class = CustomSetPasswordForm
    template_name = ''
    success_url = reverse_lazy('')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            _('Your password has been reset successfully.')
        )
        return response
    

class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'account/password_reset_complete.html'


class EmailVerificationView(generic.View):
    
    def get(self, request, code):
        user = get_object_or_404(User, email_active_code=code)
        
        if user.is_active:
            messages.info(request, _('Your email is already verified.'))
            return redirect('')
        
        if not EmailVerificationService(user):
            messages.error(request, _('Invalid or expired verification code.'))
            return redirect('')
        

        user.email_active_code = ''
        user.is_email_verified = True
        user.is_active = True

        user.save(update_fields=[
            'email_active_code', 'is_email_verified', 'is_active'
        ])

        messages.success(request, _('Your email has been successfully verified.'))

        return redirect('')