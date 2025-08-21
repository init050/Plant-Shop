from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class EmailChangeForm(forms.Form):
    new_email = forms.EmailField(
        label=_('New Email Address'),
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 transition duration-150 ease-in-out',
            'placeholder': 'Enter new email address'
        })
    )
    
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
    
    def clean_new_email(self):
        new_email = self.cleaned_data['new_email']
        
        if new_email == self.user.email:
            raise forms.ValidationError(_('New email must be different from current email.'))
        
        if User.objects.filter(email=new_email).exists():
            raise forms.ValidationError(_('This email address is already in use.'))
        
        return new_email


class OldEmailVerificationForm(forms.Form):
    verification_code = forms.CharField(
        label=_('Verification Code'),
        max_length=6,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 transition duration-150 ease-in-out text-center text-2xl tracking-widest',
            'placeholder': '123456',
            'maxlength': '6'
        })
    )
    
    def clean_verification_code(self):
        code = self.cleaned_data['verification_code']
        if not code.isdigit() or len(code) != 6:
            raise forms.ValidationError(_('Please enter a valid 6-digit code.'))
        return code