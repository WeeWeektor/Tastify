from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from shared import BaseRedisService
from shared.decorators import cache_user_data
from .models import OrderHistoryItem
from .serializers import OrderHistoryItemSerializer

order_history_cache = BaseRedisService(
    redis_url=settings.REDIS_URL,
    prefix="user_order_history",
    ttl_seconds=300
)


class OrderHistoryListView(generics.ListAPIView):
    serializer_class = OrderHistoryItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return OrderHistoryItem.objects.filter(user_id=self.request.user.id)

    @extend_schema(
        tags=['Order History'],
        summary="Список історії замовлень користувача",
        description="Отримати список замовлень користувача з кешуванням результатів на 5 хвилин."
    )
    @cache_user_data(redis_client=order_history_cache)
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
