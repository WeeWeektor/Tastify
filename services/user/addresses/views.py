from django.conf import settings
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets, permissions

from shared import BaseRedisService
from shared.decorators import cache_user_data, invalidate_user_data_cache
from .models import DeliveryAddress
from .serializers import AddressSerializer
from .services import DeliveryAddressService

address_cache = BaseRedisService(
    redis_url=settings.REDIS_URL,
    prefix="address_list",
    ttl_seconds=600
)


@extend_schema_view(
    list=extend_schema(summary="Отримання списку адрес користувача"),
    retrieve=extend_schema(summary="Отримання конкретної адреси за ID"),
    create=extend_schema(summary="Створення нової адреси"),
    update=extend_schema(summary="Повне оновлення адреси"),
    partial_update=extend_schema(summary="Часткове оновлення адреси"),
    destroy=extend_schema(summary="Видалення адреси")
)
@extend_schema(tags=['Delivery Address'])
class AddressViewSet(viewsets.ModelViewSet):
    lookup_field = 'id'
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return DeliveryAddress.objects.filter(user_id=self.request.user.id)

    @cache_user_data(redis_client=address_cache)
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def perform_create(self, serializer):
        user_id = str(self.request.user.id)

        instance = DeliveryAddressService.create_address(user_id, serializer.validated_data)
        serializer.instance = instance

        invalidate_user_data_cache(redis_client=address_cache, user_id=user_id)

    def perform_update(self, serializer):
        user_id = str(self.request.user.id)

        instance = DeliveryAddressService.update_address(serializer.instance, serializer.validated_data)
        serializer.instance = instance

        invalidate_user_data_cache(redis_client=address_cache, user_id=user_id)

    def perform_destroy(self, instance):
        user_id = str(self.request.user.id)

        instance.delete()

        invalidate_user_data_cache(redis_client=address_cache, user_id=user_id)
