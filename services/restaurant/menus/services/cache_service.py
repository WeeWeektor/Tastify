from django.conf import settings

from shared.redis_client import BaseRedisService

public_menu_list_cache = BaseRedisService(
    redis_url=settings.REDIS_URL,
    prefix="public_menu_list",
    ttl_seconds=3600
)

public_menu_detail_cache = BaseRedisService(
    redis_url=settings.REDIS_URL,
    prefix="public_menu_detail",
    ttl_seconds=3600
)
