from django.conf import settings

from shared import BaseRedisService

order_history_cache = BaseRedisService(
    redis_url=settings.REDIS_URL,
    prefix="user_order_history",
    ttl_seconds=300
)
