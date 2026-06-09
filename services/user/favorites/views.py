from django.conf import settings
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets, permissions, mixins

from shared.redis_client import BaseRedisService
from shared.decorators.cache_user_data_decorator import cache_user_data, invalidate_user_data_cache
from .models import FavoriteRestaurant
from .serializers import FavoriteRestaurantSerializer
from .services import FavoriteRestaurantService

favorites_cache = BaseRedisService(
    redis_url=settings.REDIS_URL,
    prefix="user_favorites",
    ttl_seconds=600
)


@extend_schema(tags=['Favorite Restaurants'])
@extend_schema_view(
    list=extend_schema(summary="Список улюблених ресторанів"),
    retrieve=extend_schema(summary="Отримати запис улюбленого за ID"),
    create=extend_schema(summary="Додати ресторан в улюблені"),
    destroy=extend_schema(summary="Видалити ресторан з улюблених")
)
class FavoriteRestaurantViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    lookup_field = 'id'
    serializer_class = FavoriteRestaurantSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return FavoriteRestaurant.objects.filter(user_id=self.request.user.id)

    @cache_user_data(redis_client=favorites_cache)
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def perform_create(self, serializer):
        user_id = str(self.request.user.id)

        instance = FavoriteRestaurantService.add_favorite_restaurant(user_id, serializer.validated_data)
        serializer.instance = instance

        invalidate_user_data_cache(redis_client=favorites_cache, user_id=user_id)

    def perform_destroy(self, instance):
        user_id = str(self.request.user.id)

        FavoriteRestaurantService.remove_favorite_restaurant(instance)

        invalidate_user_data_cache(redis_client=favorites_cache, user_id=user_id)
