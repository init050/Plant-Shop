from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.translation import gettext_lazy as _
import logging

logger = logging.getLogger(__name__)

class EmailVerificationSender:
    @staticmethod
    def send(user, token):
        try:
            context = {
                'user': user,
                'verification_url': f"{settings.SITE_URL}/verify-email/{token}/",
                'expiry_hours': 24
            }
            html_message = render_to_string('account_module/email/verification_email.html', context)
            plain_message = render_to_string('account_module/email/verification_email.txt', context)

            send_mail(
                subject=_('Verify your email address'),
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )
            return True
        except Exception as e:
            logger.error(f"Error sending verification email: {str(e)}")
            return False 