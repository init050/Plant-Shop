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
    # The password fields are defined here directly, instead of the model,
    # because the model should store a hashed password, not the plain text.
    # This form handles the temporary plain-text passwords and ensures they match.
    password1 = forms.CharField(
        label=_('Password'),
        widget=forms.PasswordInput(render_value=False),
        validators=[StrongPasswordValidator()],
        help_text=_('Include at least one uppercase letter, one number, and one special character.')
    )
    password2 = forms.CharField( 
        label=_('Confirm Password'),
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

    def clean(self):
        # The clean method is the correct place to validate fields that depend on each other,
        # like ensuring password1 and password2 match.
        cleaned_data = super().clean()
        password = cleaned_data.get('password1')
        password_confirm = cleaned_data.get('password2')
        if password and password_confirm and password != password_confirm:
            self.add_error('password2', _('Passwords do not match.'))
        return cleaned_data
    
    @transaction.atomic
    def save(self, commit=True):
        # We override the save method to handle the password hashing.
        # The form's cleaned_data contains the plain-text password, which we use
        # to set the user's password correctly before saving the instance.
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
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
        # This form is designed to only allow updates to the email and avatar fields.
        # Disabling other fields here enforces this rule at the form level,
        # preventing accidental updates to fields like username or phone number.
        for field_name in self.fields:
            if field_name not in ['email', 'avatar']:
                self.fields[field_name].disabled = True

