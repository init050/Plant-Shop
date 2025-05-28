from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta

class EmailVerificationRepository:
    CACHE_PREFIX = 'email_verification_'
    EXPIRY = timedelta(hours=24)

    @classmethod
    def store(cls, user_id, token):
        key = f"{cls.CACHE_PREFIX}{user_id}"
        cache.set(key, {
            'token': token,
            'created_at': timezone.now(),
            'attempts': 0,
        }, timeout=int(cls.EXPIRY.total_seconds()))

    @classmethod
    def get(cls, user_id):
        return cache.get(f"{cls.CACHE_PREFIX}{user_id}")

    @classmethod
    def delete(cls, user_id):
        cache.delete(f"{cls.CACHE_PREFIX}{user_id}")

    @classmethod
    def increment_attempts(cls, user_id):
        key = f"{cls.CACHE_PREFIX}{user_id}"
        data = cache.get(key)
        if data:
            data['attempts'] += 1
            cache.set(key, data, timeout=int(cls.EXPIRY.total_seconds()))
            return data['attempts']
        return 0 