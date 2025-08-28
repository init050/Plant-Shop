from typing import Any
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.contrib.auth.base_user import AbstractBaseUser
from django.db.models import Q
from django.contrib.auth.hashers import make_password


User = get_user_model()


class EmailOrUsernameBackend(ModelBackend):
    '''
    Custom authentication backend.

    This allows users to log in using either their email address or their username.
    '''

    def authenticate(self, request, username, password, **kwargs):
        if username is None or password is None:
            return None

        try:
            user = User.objects.get(
                Q(email__iexact=username) | Q(username__iexact=username)
            )

            if user.check_password(password):
                return user

        except User.DoesNotExist:
            # Run the password hasher once to prevent timing attacks
            make_password(password)

        return None
    
    def get_user(self, user_id: int):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None