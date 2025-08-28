from datetime import timedelta

from django.core.cache import cache
from django.utils import timezone


class EmailVerificationRepository:
    """
    A repository class that abstracts the caching mechanism for storing
    email verification data. It provides a clean, centralized interface
    for interacting with the cache for this specific purpose.
    """
    # Using the token as the cache key is a strategic choice.
    # It allows us to retrieve the verification record with just the token,
    # which is essential since the token is the only piece of information
    # we'll have from the verification URL.
    CACHE_PREFIX = 'email_verification_'
    EXPIRY = timedelta(hours=24)

    @classmethod
    def store(cls, user_id, token):
        """
        Stores verification data in the cache.
        """
        key = '{}{}'.format(cls.CACHE_PREFIX, token)
        cache.set(
            key,
            {
                'user_id': user_id,
                'created_at': timezone.now(),
                'attempts': 0,
            },
            timeout=int(cls.EXPIRY.total_seconds())
        )

    @classmethod
    def get(cls, token):
        """
        Retrieves verification data from the cache.
        """
        key = '{}{}'.format(cls.CACHE_PREFIX, token)
        return cache.get(key)

    @classmethod
    def delete(cls, token):
        """
        Deletes verification data from the cache.
        """
        key = '{}{}'.format(cls.CACHE_PREFIX, token)
        cache.delete(key)

    @classmethod
    def increment_attempts(cls, token):
        """
        Increments the attempt counter for a given verification token.
        """
        key = '{}{}'.format(cls.CACHE_PREFIX, token)
        data = cache.get(key)

        if data:
            data['attempts'] += 1
            cache.set(key, data, timeout=int(cls.EXPIRY.total_seconds()))
            return data['attempts']

        return 0 