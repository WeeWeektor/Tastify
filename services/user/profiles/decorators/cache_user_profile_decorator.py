import json
from functools import wraps

from django.conf import settings
from rest_framework.response import Response

from shared import BaseRedisService

profile_cache = BaseRedisService(
    redis_url=settings.REDIS_URL,
    prefix="user_profile",
    ttl_seconds=3600
)


def cache_user_profile():
    """
        Декоратор для кешування профілю користувача.
        Перехоплює GET-запит: віддає з Redis або виконує view і записує результат.
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(view_instance, request, *args, **kwargs):
            user_id = str(request.user.id)

            cached_data = profile_cache.get_value(user_id)
            if cached_data:
                return Response(json.loads(cached_data))

            response = view_func(view_instance, request, *args, **kwargs)

            if response.status_code == 200:
                profile_cache.store(key=user_id, value=json.dumps(response.data))

            return response

        return _wrapped_view

    return decorator


def invalidate_profile_cache(user_id: str):
    profile_cache.delete(user_id)
