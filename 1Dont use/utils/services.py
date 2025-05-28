from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

class UserService:
    @staticmethod
    def create_user(username, email, password, phone_number=None):
        """Create a new user with email verification"""
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                phone_number=phone_number
            )
            user.generate_email_verification_code()
            return user
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            raise

    @staticmethod
    def verify_email(user, code):
        """Verify user's email"""
        if user.email_active_code == code:
            user.is_email_verified = True
            user.save()
            return True
        return False

    @staticmethod
    def send_verification_email(user):
        """Send verification email to user"""
        try:
            subject = _('Verify your email address')
            message = _('Please click the following link to verify your email: {verification_url}').format(
                verification_url=f"{settings.SITE_URL}/verify-email/{user.email_active_code}/"
            )
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            return True
        except Exception as e:
            logger.error(f"Error sending verification email: {str(e)}")
            return False

    @staticmethod
    def send_password_reset_email(user):
        """Send password reset email to user"""
        try:
            token = user.generate_password_reset_token()
            subject = _('Reset your password')
            message = _('Please click the following link to reset your password: {reset_url}').format(
                reset_url=f"{settings.SITE_URL}/reset-password/{token}/"
            )
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            return True
        except Exception as e:
            logger.error(f"Error sending password reset email: {str(e)}")
            return False

class ProfileService:
    @staticmethod
    def update_profile(user, data):
        """Update user profile"""
        try:
            for key, value in data.items():
                setattr(user, key, value)
            user.save()
            return user
        except Exception as e:
            logger.error(f"Error updating profile: {str(e)}")
            raise

    @staticmethod
    def update_avatar(user, avatar):
        """Update user avatar"""
        try:
            user.avatar = avatar
            user.save()
            return user
        except Exception as e:
            logger.error(f"Error updating avatar: {str(e)}")
            raise

class SecurityService:
    @staticmethod
    def update_last_login_ip(user, ip_address):
        """Update user's last login IP"""
        try:
            user.last_login_ip = ip_address
            user.save()
            return user
        except Exception as e:
            logger.error(f"Error updating last login IP: {str(e)}")
            raise

    @staticmethod
    def validate_password_reset_token(token):
        """Validate password reset token"""
        try:
            user = User.objects.get(password_reset_token=token)
            if user.is_password_reset_token_valid():
                return user
            return None
        except User.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error validating password reset token: {str(e)}")
            return None

class SocialAuthService:
    @staticmethod
    def update_social_links(user, social_links):
        """Update user's social media links"""
        try:
            user.social_links = social_links
            user.save()
            return user
        except Exception as e:
            logger.error(f"Error updating social links: {str(e)}")
            raise

    @staticmethod
    def get_social_links(user):
        """Get user's social media links"""
        return user.social_links 