import logging
from django.core.mail import send_mail
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.contrib.auth import get_user_model
from ..utils.token_generator import TokenGenerator
from ..utils.repository import EmailVerificationRepository

logger = logging.getLogger(__name__)
User = get_user_model()


class EmailVerificationService:
    MAX_ATTEMPTS = 3

    @classmethod
    def send_verification_email(cls, request, user):
        # This service is responsible for the entire email verification flow.
        # It generates a token, stores it, and sends an email.
        # Passing the `request` object here is necessary to build an absolute URL,
        # ensuring the user gets a clickable link that works regardless of the domain.
        try:
            token = TokenGenerator.generate()
            EmailVerificationRepository.store(user.id, token)

            verification_path = reverse('account_module:verify_email', kwargs={'token': token})
            verification_url = request.build_absolute_uri(verification_path)

            subject = _('Verify your email address')
            message = _(f'Please click the following link to verify your email: {verification_url}')

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
    def verify(cls, token):
        # This method handles the core verification logic. It's now self-contained.
        # It retrieves data using the token, finds the user, and activates them.
        # This decouples the verification logic from the view.
        try:
            data = EmailVerificationRepository.get(token)
            if not data:
                return False, _('Verification link expired or invalid.')

            user = User.objects.filter(id=data.get('user_id')).first()
            if not user:
                return False, _('User not found for this verification request.')

            # The original implementation checked for the token match inside the service,
            # but since the token is now the key in our cache, `EmailVerificationRepository.get(token)`
            # succeeding is proof enough that the token is valid. An invalid token would simply return None.

            user.activate()
            EmailVerificationRepository.delete(token)

            return True, _('Email successfully verified.')
        except Exception as e:
            logger.error(f"Failed to verify email with token {token}: {str(e)}")
            return False, _('An unexpected error occurred during verification.')
