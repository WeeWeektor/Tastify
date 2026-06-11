import json
from functools import wraps

from django.core.serializers.json import DjangoJSONEncoder
from rest_framework.response import Response

from shared.redis_client import BaseRedisService


def cache_public_data(redis_client: BaseRedisService, encoder_class=DjangoJSONEncoder):
    """
    Декоратор для кешування публічних даних (наприклад, списку ресторанів).
    Кеш є спільним для всіх користувачів і залежить тільки від URL, параметрів та мови.
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(view_instance, request, *args, **kwargs):
            path = request.path

            lang = getattr(request, 'LANGUAGE_CODE', 'en')
            query_string = request.query_params.urlencode()

            cache_suffix = f"path_{path}:lang_{lang}:qs_{query_string}"

            cached_data = redis_client.get_value(cache_suffix)
            if cached_data:
                return Response(json.loads(cached_data))

            response = view_func(view_instance, request, *args, **kwargs)

            if response.status_code == 200:
                redis_client.store(
                    key=cache_suffix,
                    value=json.dumps(response.data, cls=encoder_class)
                )

            return response

        return _wrapped_view

    return decorator


def invalidate_public_data_cache(redis_client: BaseRedisService, path_prefix: str):
    """
    Видаляє кеш для конкретного публічного ендпоінта.
    Наприклад, invalidate_public_data_cache(redis, '/api/v1/restaurants/')
    """
    redis_client.delete_by_pattern(f"path_{path_prefix}*")
