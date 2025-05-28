from django import forms
from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from phonenumber_field.formfields import PhoneNumberField
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Div, Submit
from .. models import User
from .validators import StrongPasswordValidator, AvatarValidator


class UserRegistrationForm(ModelForm):

    password1 = forms.CharField(
        label=_('Password'),
        widget=forms.PasswordInput(render_value=False),
        validators=[StrongPasswordValidator()],
        help_text=_('Include at least one uppercase letter, one number, and one special character.')
    )

    password2 = forms.CharField( 
        label=_('Password'),
        widget=forms.PasswordInput(render_value=False)
    )

    phone_number = PhoneNumberField(
        label=_('Phone number'),
        region='IR',
        help_text=_('Like : +989123456789')
    )

    avatar = forms.ImageField(
        label=_('Avatar'),
        validators=[AvatarValidator().validate],
        required=False,
    )

    
    class Meta:

        model = User
        fields = ['email', 'username', 'phone_number', 'avatar']
        widgets = {
            'email':forms.EmailInput(attrs={'placeholder' : 'plant@example.com'}),
            'username':forms.TextInput(attrs={'placeholder': _('username')})
        }

    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(
                Column('email', css_class='form-group col-md-6'),
                Column('username', css_class='form-group col-md-6'),
                css_class='form-row'
            ),
            Row(
                Column('password1', css_class='form-group col-md-6'),
                Column('password2', css_class='form-group col-md-6'),
                css_class='form-row'
            ),
            Row(
                Column('avatar', css_class='form-group col-md-6'),
                Column('phone_number', css_class='form-group col-md-6'),
                css_class='form-row'
            ),
            Div(Submit('submit', _('Register')), css_class='mt-3 text-right')
        )

    
    def clean_email(self):
        email = self.cleaned_data.get('email').lower()
        qs = User.objects.filter(email=email)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError(_('This email has already been registered'))
        return email
    
    def clean_username(self):
        username = self.cleaned_data.get('username').lower()
        qs = User.objects.filter(username=username)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError(_('This username has already been registered'))
        return username
    
    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        qs = User.objects.filter(phone_number=phone_number)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError(_('This phone number has already been registered'))
        return phone_number
    
    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password1')
        p2 = cleaned.get('password2')
        if p1 and p2 and p1 != p2:
            self.add_error('password2',_('Passwords do not match'))


    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        # user.generate_email_verification_code() 
        if commit:
            user.save()
        return user
    


class UserProfileForm(ModelForm):
    class Meta:
        model = User
        fields = ['avatar', 'phone_number', 'email', 'username']
        widgets = {
            'email': forms.EmailInput(attrs={'placeholder': 'plant@example.com'}),
            'username': forms.TextInput(attrs={'placeholder': _('username')}),
            'phone_number': forms.TextInput(attrs={'placeholder': '+989123456789'}),
            'avatar': forms.FileInput(attrs={'accept': 'image/*'})
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for filed_name in self.fields:
            if filed_name != 'email' and filed_name != 'avatar':
                self.fields[filed_name].disabled = True

