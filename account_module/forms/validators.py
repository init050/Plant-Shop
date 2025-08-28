from django.core import validators
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class StrongPasswordValidator(validators.RegexValidator):
    # This regex enforces a password policy:
    # - (?=.*[A-Z]): At least one uppercase letter.
    # - (?=.*\d): At least one digit.
    # - (?=.*[@$!%*?&]): At least one special character.
    # - [A-Za-z\d@$!%*?&]{8,}: At least 8 characters long, consisting of letters, digits, and the specified special characters.
    regex = r'^(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'
    message = _(
        'The password must be at least 8 characters long and include '
        'at least one uppercase letter, one number, and one special character.'
    )
    code = 'password_no_strong'


class AvatarValidator:
    """
    A custom validator for avatar images that checks for file size and valid extensions.
    """

    def validate_avatar_size(self, value):
        # Ensure the avatar file size does not exceed 5MB.
        max_size = 5 * 1024 * 1024
        if value.size > max_size:
            raise ValidationError(
                _('Avatar file size must be no more than 5MB.')
            )

    def validate_avatar_extension(self, value):
        ext = value.name.split('.')[-1].lower()
        if ext not in ['jpg', 'jpeg', 'png']:
            raise ValidationError(
                _('Avatar must be a valid image file (jpg, jpeg, png).')
            )

    def validate(self, value):
        # This method is called by the form field.
        # It runs all individual validation checks.
        self.validate_avatar_size(value)
        self.validate_avatar_extension(value)