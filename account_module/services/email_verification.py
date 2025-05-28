import logging
from django.core.mail import send_mail
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from ..utils.token_generator import TokenGenerator
from ..utils.repository import EmailVerificationRepository

logger = logging.getLogger(__name__)


class EmailVerificationService:
    """
    Service class for handling email verification operations at a senior level.
    Combines token generation, repository logic, and email sending.
    """

    MAX_ATTEMPTS = 3

    @classmethod
    def send_verification_email(cls, user):
        """
        Generate a token, store it, and send it to user's email.

        Args:
            user: User instance

        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        try:
            token = TokenGenerator.generate()
            EmailVerificationRepository.store(user.id, token)

            subject = _('Verify your email address')
            message = _(f'Please use the following code to verify your email: {token}')

            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send verification email to {user.email}: {str(e)}")
            return False

    @classmethod
    def verify(cls, user, token):
        """
        Verify the token provided by the user.

        Args:
            user: User instance
            token: The token string to be verified

        Returns:
            tuple: (bool success, str message)
        """
        try:
            data = EmailVerificationRepository.get(user.id)
            if not data:
                return False, _('Verification link expired or invalid.')

            if data['token'] != token:
                attempts = EmailVerificationRepository.increment_attempts(user.id)
                if attempts >= cls.MAX_ATTEMPTS:
                    EmailVerificationRepository.delete(user.id)
                    return False, _('Too many invalid attempts.')
                return False, _('Invalid token.')

            user.is_email_verified = True
            user.email_active_code = ''
            user.save(update_fields=['is_email_verified', 'email_active_code'])
            EmailVerificationRepository.delete(user.id)

            return True, _('Email successfully verified.')
        except Exception as e:
            logger.error(f"Failed to verify email for user {user.email}: {str(e)}")
            return False, _('An unexpected error occurred during verification.')
