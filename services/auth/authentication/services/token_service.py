from django.conf import settings
from shared import BaseRedisService

pre_auth_service = BaseRedisService(
    redis_url=settings.REDIS_URL,
    prefix="pre_auth",
    ttl_seconds=300
)

email_verification_service = BaseRedisService(
    redis_url=settings.REDIS_URL,
    prefix="email_verification",
    ttl_seconds=24 * 3600
)

password_reset_service = BaseRedisService(
    redis_url=settings.REDIS_URL,
    prefix="password_reset",
    ttl_seconds=3600
)

token_blacklist_service = BaseRedisService(
    redis_url=settings.REDIS_URL,
    prefix="blacklist",
    ttl_seconds=7 * 24 * 3600
)
