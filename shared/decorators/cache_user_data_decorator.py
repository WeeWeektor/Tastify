import json
from functools import wraps

from django.core.serializers.json import DjangoJSONEncoder
from rest_framework.response import Response

from shared import BaseRedisService


def cache_user_data(redis_client: BaseRedisService, encoder_class=DjangoJSONEncoder):
    """
    Універсальний декоратор для кешування даних користувача.
    Адаптований для використання у будь-якому мікросервісі.
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(view_instance, request, *args, **kwargs):
            user_id = None
            if hasattr(request, 'user') and getattr(request.user, 'id', None):
                user_id = str(request.user.id)
            elif hasattr(request, 'user_context') and isinstance(request.user_context, dict):
                user_id = str(request.user_context.get('user_id'))

            if not user_id:
                return view_func(view_instance, request, *args, **kwargs)

            cached_data = redis_client.get_value(user_id)
            if cached_data:
                return Response(json.loads(cached_data))

            response = view_func(view_instance, request, *args, **kwargs)

            if response.status_code == 200:
                redis_client.store(
                    key=user_id,
                    value=json.dumps(response.data, cls=encoder_class)
                )

            return response

        return _wrapped_view

    return decorator


def invalidate_user_data_cache(redis_client: BaseRedisService, user_id: str):
    redis_client.delete(user_id)
