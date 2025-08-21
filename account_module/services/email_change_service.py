import logging
from django.core.mail import send_mail
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from ..utils.verification_code_generator import VerificationCodeGenerator
from .email_verification import EmailVerificationService

logger = logging.getLogger(__name__)
User = get_user_model()


class EmailChangeService:
    @classmethod
    def initiate_email_change(cls, request, user, new_email):
        # Two-step verification: old email gets 6-digit code, new email gets verification link
        try:
            # Generate 6-digit code for old email
            old_email_code = VerificationCodeGenerator.generate_6_digit_code()
            
            # Store the verification code and new email
            user.old_email_verification_code = old_email_code
            user.pending_email = new_email
            user.old_email_verified = False
            user.email_change_initiated_at = timezone.now()
            user.is_email_verified = False
            user.save(update_fields=[
                'old_email_verification_code', 'pending_email', 'old_email_verified',
                'email_change_initiated_at', 'is_email_verified'
            ])
            
            # Send 6-digit code to old email
            cls._send_old_email_verification(user, old_email_code)
            
            logger.info(f"Email change initiated for user {user.id}: {user.email} -> {new_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initiate email change for user {user.id}: {str(e)}")
            return False
    
    @classmethod
    def _send_old_email_verification(cls, user, code):
        # Send 6-digit verification code to current email
        subject = _('Verify Email Change Request')
        message = f"""
Hello {user.username or user.email}!

Someone has requested to change the email address for your account.

Your verification code is: {code}

If you didn't request this change, please ignore this email and consider changing your password.

This code will expire in 15 minutes.

© {getattr(settings, 'SITE_NAME', 'Plant Shop')} - All rights reserved
"""
        
        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com'),
            recipient_list=[user.email],
            fail_silently=False,
        )
        
        logger.info(f"Old email verification code sent to {user.email}")
    
    @classmethod
    def verify_old_email(cls, user, code):
        # Verify the 6-digit code from old email
        if not user.old_email_verification_code or not user.pending_email:
            return False, _('No pending email change found.')
        
        # Check if code has expired (15 minutes)
        if user.email_change_initiated_at:
            time_diff = timezone.now() - user.email_change_initiated_at
            if time_diff.total_seconds() > 900:  # 15 minutes
                return False, _('Verification code has expired.')
        
        if user.old_email_verification_code != code:
            return False, _('Invalid verification code.')
        
        # Mark old email as verified
        user.old_email_verified = True
        user.save(update_fields=['old_email_verified'])
        
        logger.info(f"Old email verified for user {user.id}")
        return True, _('Old email verified successfully.')
    
    @classmethod
    def send_new_email_verification(cls, request, user):
        # Send verification link to new email after old email is verified
        if not user.old_email_verified or not user.pending_email:
            return False
        
        # Use existing email verification service for new email
        return EmailVerificationService.send_verification_email(request, user, user.pending_email)
    
    @classmethod
    def complete_email_change(cls, user):
        # Complete the email change process
        if user.old_email_verified and user.pending_email:
            user.activate_email_change()
            logger.info(f"Email change completed for user {user.id}")
            return True
        return False