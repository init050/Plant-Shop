import logging
from django.core.mail import send_mail
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from ..utils.token_generator import TokenGenerator
from ..utils.repository import EmailVerificationRepository

logger = logging.getLogger(__name__)
User = get_user_model()


class EmailVerificationService:
    MAX_ATTEMPTS = 3

    @classmethod
    def send_verification_email(cls, request, user, target_email=None):
        try:
            token = TokenGenerator.generate()
            
            EmailVerificationRepository.store(user.id, token)
            
            user.email_active_code = token
            user.save(update_fields=['email_active_code'])

            email_to_send = target_email or user.email
            
            verification_path = reverse('account_module:verify_email', kwargs={'token': token})
            verification_url = request.build_absolute_uri(verification_path)

            context = {
                'user': user,
                'verification_url': verification_url,
                'site_name': getattr(settings, 'SITE_NAME', 'Plant Shop'),
                'target_email': email_to_send,
                'is_email_change': target_email is not None,
            }
            
            # Simple email content without template file
            subject = _('Verify your email address')
            if target_email:
                subject = _('Verify your new email address')

            if target_email:
                message = f"""
Hello {user.username or user.email}!

You have requested to change your email address. To complete this process and verify your new email, please click the link below:

{verification_url}

New Email: {email_to_send}

Important Notes:
- This link is valid for 24 hours
- Until verified, your old email will remain active

If you didn't make this request, please ignore this email.

© {context['site_name']} - All rights reserved
"""
            else:
                message = f"""
Hello {user.username or user.email}!

Welcome! To complete your registration and activate your account, please verify your email address:

{verification_url}

Important Notes:
- This link is valid for 24 hours
- Without verification, your account will remain inactive

If you didn't make this request, please ignore this email.

© {context['site_name']} - All rights reserved
"""

            send_mail(
                subject=subject,
                message=message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com'),
                recipient_list=[email_to_send],
                fail_silently=False,
            )
            
            logger.info(f"Verification email sent successfully to {email_to_send} for user {user.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send verification email to {target_email or user.email}: {str(e)}")
            return False

    @classmethod
    def send_verification_email_for_change(cls, request, user, new_email):
        return cls.send_verification_email(request, user, new_email)

    @classmethod
    def verify(cls, token):
        try:
            data = EmailVerificationRepository.get(token)
            if not data:
                return False, _('Verification link expired or invalid.')

            user = User.objects.filter(id=data.get('user_id')).first()
            if not user:
                return False, _('User not found for this verification request.')

            if user.email_active_code != token:
                return False, _('Invalid verification token.')

            if data.get('attempts', 0) >= cls.MAX_ATTEMPTS:
                return False, _('Too many verification attempts. Please request a new verification email.')

            user.activate()
            EmailVerificationRepository.delete(token)

            logger.info(f"Email verification successful for user {user.id}")
            return True, _('Email successfully verified. You can now login.')
            
        except Exception as e:
            logger.error(f"Failed to verify email with token {token}: {str(e)}")
            return False, _('An unexpected error occurred during verification.')

    @classmethod
    def increment_attempts(cls, token):
        return EmailVerificationRepository.increment_attempts(token)