from django.core import validators
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError


class StrongPasswordValidator(validators.RegexValidator):
    regex = r'^(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'
    message = _(
        'The password must be at least 8 characters long and include at least one uppercase letter, one number, and one special character.'
        )
    code = 'password_no_strong'



class AvatarValidator:
    def validate_avatar_size(self, value):
        if value.size > 5 * 1024 * 1024:  
            raise ValidationError(_('Avatar file size must be no more than 5MB.'))

    def validate_avatar_extension(self, value):
        ext = value.name.split('.')[-1].lower()
        if ext not in ['jpg', 'jpeg', 'png']:
            raise ValidationError(_('Avatar must be a valid image file (jpg, jpeg, png).'))
        
    def validate(self, value):
        self.validate_avatar_size(value)
        self.validate_avatar_extension(value)