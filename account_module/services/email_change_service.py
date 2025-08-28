import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from ..utils.verification_code_generator import VerificationCodeGenerator
from .email_verification import EmailVerificationService

logger = logging.getLogger(__name__)
User = get_user_model()


class EmailChangeService:
    """
    Handles the business logic for securely changing a user's email address.
    This service uses a two-factor process:
    1. A 6-digit code is sent to the user's current (old) email address.
    2. A verification link is sent to the new email address.
    Both must be completed to finalize the change.
    """

    @classmethod
    def initiate_email_change(cls, request, user, new_email):
        """
        Starts the email change process.
        It generates and sends a 6-digit code to the user's current email.
        """
        try:
            old_email_code = VerificationCodeGenerator.generate_6_digit_code()

            # Store the verification data on the user model.
            user.old_email_verification_code = old_email_code
            user.pending_email = new_email
            user.old_email_verified = False
            user.email_change_initiated_at = timezone.now()
            user.is_email_verified = False
            user.save(
                update_fields=[
                    'old_email_verification_code',
                    'pending_email',
                    'old_email_verified',
                    'email_change_initiated_at',
                    'is_email_verified'
                ]
            )

            cls._send_old_email_verification(user, old_email_code)

            logger.info(
                'Email change initiated for user {}: {} -> {}'.format(
                    user.id, user.email, new_email
                )
            )
            return True

        except Exception as e:
            logger.error(
                'Failed to initiate email change for user {}: {}'.format(
                    user.id, str(e)
                )
            )
            return False

    @classmethod
    def _send_old_email_verification(cls, user, code):
        """Sends the 6-digit verification code to the user's current email."""
        subject = _('Verify Email Change Request')
        message = _(
            'Hello {username}!\n\n'
            'Someone has requested to change the email address for your account.\n\n'
            'Your verification code is: {code}\n\n'
            "If you didn't request this change, please ignore this email and consider changing your password.\n\n"
            'This code will expire in 15 minutes.\n\n'
            '© {site_name} - All rights reserved'
        ).format(
            username=(user.username or user.email),
            code=code,
            site_name=getattr(settings, 'SITE_NAME', 'Plant Shop')
        )

        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com'),
            recipient_list=[user.email],
            fail_silently=False,
        )

        logger.info('Old email verification code sent to {}'.format(user.email))

    @classmethod
    def verify_old_email(cls, user, code):
        """
        Verifies the 6-digit code sent to the old email.
        Returns a tuple: (bool_success, str_message).
        """
        if not user.old_email_verification_code or not user.pending_email:
            return False, _('No pending email change found.')

        # Check if the code has expired (15-minute validity).
        if user.email_change_initiated_at:
            time_diff = timezone.now() - user.email_change_initiated_at
            if time_diff.total_seconds() > 900:
                return False, _('Verification code has expired.')

        if user.old_email_verification_code != code:
            return False, _('Invalid verification code.')

        # Mark the old email as verified to proceed to the next step.
        user.old_email_verified = True
        user.save(update_fields=['old_email_verified'])

        logger.info('Old email verified for user {}'.format(user.id))
        return True, _('Old email verified successfully.')

    @classmethod
    def send_new_email_verification(cls, request, user):
        """
        Sends a verification link to the new email address.
        This reuses the main EmailVerificationService.
        """
        if not user.old_email_verified or not user.pending_email:
            return False

        return EmailVerificationService.send_verification_email(
            request, user, user.pending_email
        )

    @classmethod
    def complete_email_change(cls, user):
        """
        Finalizes the email change process after all verifications are complete.
        """
        if user.old_email_verified and user.pending_email:
            user.activate_email_change()
            logger.info('Email change completed for user {}'.format(user.id))
            return True
        return False