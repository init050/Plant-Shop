from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta

class EmailVerificationRepository:
    # Using the token as the cache key is a strategic choice.
    # It allows us to retrieve the verification record with just the token,
    # which is essential since the token is the only piece of information
    # we'll have from the verification URL.
    CACHE_PREFIX = 'email_verification_'
    EXPIRY = timedelta(hours=24)

    @classmethod
    def store(cls, user_id, token):
        key = f"{cls.CACHE_PREFIX}{token}"
        cache.set(key, {
            'user_id': user_id,
            'created_at': timezone.now(),
            'attempts': 0,
        }, timeout=int(cls.EXPIRY.total_seconds()))

    @classmethod
    def get(cls, token):
        return cache.get(f"{cls.CACHE_PREFIX}{token}")

    @classmethod
    def delete(cls, token):
        cache.delete(f"{cls.CACHE_PREFIX}{token}")

    @classmethod
    def increment_attempts(cls, token):
        key = f"{cls.CACHE_PREFIX}{token}"
        data = cache.get(key)
        if data:
            data['attempts'] += 1
            cache.set(key, data, timeout=int(cls.EXPIRY.total_seconds()))
            return data['attempts']
        return 0 