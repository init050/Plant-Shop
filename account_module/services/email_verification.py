import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import strip_tags
from django.utils.translation import gettext_lazy as _

from ..utils.repository import EmailVerificationRepository
from ..utils.token_generator import TokenGenerator

logger = logging.getLogger(__name__)
User = get_user_model()


class EmailVerificationService:
    """
    Handles the business logic for user email verification.
    This includes sending verification emails and processing the verification tokens.
    """
    MAX_ATTEMPTS = 3

    @classmethod
    def send_verification_email(cls, request, user, target_email=None):
        """
        Sends a verification email with a unique token.
        Can be used for both new user registration and email change confirmation.

        Args:
            request: The Django HttpRequest object, used to build the absolute URL.
            user (User): The user instance to verify.
            target_email (str, optional): The email address to send to.
                                         If None, uses the user's primary email.
                                         Defaults to None.

        Returns:
            bool: True if the email was sent successfully, False otherwise.
        """
        try:
            token = TokenGenerator.generate()
            EmailVerificationRepository.store(user.id, token)

            user.email_active_code = token
            user.save(update_fields=['email_active_code'])

            email_to_send = target_email or user.email
            is_email_change = target_email is not None

            verification_path = reverse('account_module:verify_email', kwargs={'token': token})
            verification_url = request.build_absolute_uri(verification_path)

            site_name = getattr(settings, 'SITE_NAME', 'Plant Shop')
            
            subject = _('Verify your new email address') if is_email_change else _('Verify your email address')

            # Construct the email message based on the context (new registration vs. email change)
            if is_email_change:
                greeting = _('You have requested to change your email address. To complete this process and verify your new email, please click the link below:')
                notes = _('- This link is valid for 24 hours\n- Until verified, your old email will remain active')
            else:
                greeting = _('Welcome! To complete your registration and activate your account, please verify your email address:')
                notes = _('- This link is valid for 24 hours\n- Without verification, your account will remain inactive')

            message = _(
                'Hello {username}!\n\n'
                '{greeting}\n\n'
                '{verification_url}\n\n'
                'Important Notes:\n{notes}\n\n'
                "If you didn't make this request, please ignore this email.\n\n"
                '© {site_name} - All rights reserved'
            ).format(
                username=(user.username or user.email),
                greeting=greeting,
                verification_url=verification_url,
                notes=notes,
                site_name=site_name
            )

            send_mail(
                subject=subject,
                message=message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com'),
                recipient_list=[email_to_send],
                fail_silently=False,
            )

            logger.info('Verification email sent successfully to {} for user {}'.format(email_to_send, user.id))
            return True

        except Exception as e:
            logger.error('Failed to send verification email to {}: {}'.format(target_email or user.email, str(e)))
            return False

    @classmethod
    def send_verification_email_for_change(cls, request, user, new_email):
        """
        An alias for send_verification_email for semantic clarity when changing emails.
        """
        return cls.send_verification_email(request, user, new_email)

    @classmethod
    def verify(cls, token):
        """
        Verifies a user's email using the provided token.

        Args:
            token (str): The verification token from the email link.

        Returns:
            tuple: A tuple containing (bool_success, str_message).
        """
        try:
            data = EmailVerificationRepository.get(token)
            if not data:
                return False, _('Verification link expired or invalid.')

            user = User.objects.filter(id=data.get('user_id')).first()
            if not user:
                return False, _('User not found for this verification request.')

            if user.email_active_code != token:
                return False, _('Invalid verification token.')

            # Check if the user has exceeded the maximum number of verification attempts.
            if data.get('attempts', 0) >= cls.MAX_ATTEMPTS:
                return False, _('Too many verification attempts. Please request a new verification email.')

            user.activate()
            EmailVerificationRepository.delete(token)

            logger.info('Email verification successful for user {}'.format(user.id))
            return True, _('Email successfully verified. You can now login.')

        except Exception as e:
            logger.error('Failed to verify email with token {}: {}'.format(token, str(e)))
            return False, _('An unexpected error occurred during verification.')

    @classmethod
    def increment_attempts(cls, token):
        """
        Increments the verification attempt counter for a given token.
        """
        return EmailVerificationRepository.increment_attempts(token)