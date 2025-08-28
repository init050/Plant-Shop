from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
    PasswordResetForm,
    SetPasswordForm
)
from django.utils.translation import gettext_lazy as _

from .validators import StrongPasswordValidator


class CustomAuthenticationForm(AuthenticationForm):

    username = forms.CharField(
        label=_('Email Or Username'),
        widget=forms.TextInput(
            attrs={
                'autofocus': True,
                'placeholder': _('Enter your email or username')
            }
        )
    )
    password = forms.CharField(
        label=_('Password'),
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                'autocomplete': 'current-password',
                'placeholder': _('Password')
            }
        ),
    )


class CustomPasswordChangeForm(PasswordChangeForm):

    old_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': _('Current password')})
    )
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={'placeholder':_('New password')}
        ),
        validators=[StrongPasswordValidator()],
        help_text=_(
            'The password must be at least 8 characters long and include '
            'at least one uppercase letter, one number, and one special character.'
        )
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={'placeholder':_('Confirm new password')}
        )
    )


class CustomPasswordResetForm(PasswordResetForm):

    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={'placeholder': _('Enter your email')}
        )
    )


class CustomSetPasswordForm(SetPasswordForm):

    new_password1 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={'placeholder': _('New password')}
        ),
        validators=[StrongPasswordValidator()],
        help_text=_(
            'The password must be at least 8 characters long and include '
            'at least one uppercase letter, one number, and one special character.'
        )
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={'placeholder': _('Confirm new password')}
        )
    )