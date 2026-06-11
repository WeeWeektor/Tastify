from django.conf import settings

from shared.redis_client import BaseRedisService

restaurants_public_cache = BaseRedisService(
    redis_url=settings.REDIS_URL,
    prefix="restaurants_public",
    ttl_seconds=180
)
