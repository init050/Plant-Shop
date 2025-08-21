from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser, PermissionsMixin, BaseUserManager
)
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('The Email must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_email_verified', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        
        return self.create_user(email, password, **extra_fields)
    
class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(_('Email address'), unique=True)
    username = models.CharField(_('Username'), max_length=50, unique=True, blank=True, null=True)
    avatar = models.ImageField(_('Avatar'), upload_to='images/profiles/avatars/', blank=True, null=True)
    phone_number = models.CharField(_('Phone number'), max_length=15, blank=False, null=False)

    email_active_code = models.CharField(_('Email verification code'), max_length=200, blank=True)
    is_email_verified = models.BooleanField(_('Email verified'), default=False)
    
    pending_email = models.EmailField(_('Pending email'), blank=True, null=True)

    last_login_ip = models.GenericIPAddressField(_('Last login IP'), blank=True, null=True)    
    password_reset_token = models.UUIDField(_('Password reset token'), blank=True, null=True)
    password_reset_token_created_at = models.DateTimeField(_('Password reset token created at'), blank=True, null=True)

    is_active = models.BooleanField(_('Is active'), default=False)
    is_staff = models.BooleanField(_('Is staff'), default=False)

    date_joined = models.DateTimeField(
        _('Date joined'), auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _('Updated at'), auto_now=True
    )

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self) -> str:
        return self.email

    def activate(self):
        # This method centralizes the activation logic for a user.
        # It's used after a successful action, like email verification,
        # to ensure the user's account is marked as active and verified consistently.
        self.is_active = True
        self.is_email_verified = True
        self.email_active_code = ''
        
        if self.pending_email:
            self.email = self.pending_email
            self.pending_email = None
            
        self.save(update_fields=['is_active', 'is_email_verified', 'email_active_code', 'email', 'pending_email'])

    def can_login(self):
        return self.is_active and self.is_email_verified