import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.core.validators import validate_email
from django.utils import timezone
import hashlib
import uuid

def validate_username(username):
    """Validate username format"""
    if not re.match(r'^[\w.@+-]+$', username):
        raise ValidationError(_('Username can only contain letters, numbers, and @/./+/-/_ characters.'))
    if len(username) < 3:
        raise ValidationError(_('Username must be at least 3 characters long.'))
    if len(username) > 50:
        raise ValidationError(_('Username must be at most 50 characters long.'))

def validate_password_strength(password):
    """Validate password strength"""
    if len(password) < 8:
        raise ValidationError(_('Password must be at least 8 characters long.'))
    if not re.search(r'[A-Z]', password):
        raise ValidationError(_('Password must contain at least one uppercase letter.'))
    if not re.search(r'[a-z]', password):
        raise ValidationError(_('Password must contain at least one lowercase letter.'))
    if not re.search(r'[0-9]', password):
        raise ValidationError(_('Password must contain at least one number.'))
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        raise ValidationError(_('Password must contain at least one special character.'))

def validate_phone_number(phone_number):
    """Validate phone number format"""
    if not re.match(r'^\+?1?\d{9,15}$', phone_number):
        raise ValidationError(_('Enter a valid phone number.'))

def generate_secure_token():
    """Generate a secure token for password reset or email verification"""
    return str(uuid.uuid4())

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def is_token_expired(created_at, expiry_hours=24):
    """Check if a token is expired"""
    if not created_at:
        return True
    return (timezone.now() - created_at).total_seconds() > (expiry_hours * 3600)

def sanitize_username(username):
    """Sanitize username by removing special characters"""
    return re.sub(r'[^a-zA-Z0-9]', '', username)

def validate_social_links(social_links):
    """Validate social media links format"""
    if not isinstance(social_links, dict):
        raise ValidationError(_('Social links must be a dictionary.'))
    for platform, link in social_links.items():
        if not isinstance(platform, str) or not isinstance(link, str):
            raise ValidationError(_('Social links must be a dictionary of strings.'))
        if not link.startswith(('http://', 'https://')):
            raise ValidationError(_('Social links must be valid URLs.'))

def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip 