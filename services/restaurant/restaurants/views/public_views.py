from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema_view, extend_schema
from rest_framework import generics, permissions, filters

from shared.decorators.cache_public_data_decorator import cache_public_data
from ..filters import RestaurantFilter
from ..models import Restaurant
from ..serializers import RestaurantSerializer
from ..services import restaurants_public_cache


@extend_schema_view(
    get=extend_schema(
        tags=['Public Restaurants'],
        summary='Список активних ресторанів',
        description='Отримати список активних ресторанів з глобальним кешуванням.'
    )
)
class RestaurantListView(generics.ListAPIView):
    serializer_class = RestaurantSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter
    ]
    filterset_class = RestaurantFilter
    ordering_fields = ['rating', 'delivery_fee', 'min_order_amount', 'avg_delivery_time']
    ordering = ['-rating']

    # TODO простий пошук по назві, поки не підключено Elasticsearch
    search_fields = ['name']

    def get_queryset(self):
        return Restaurant.objects.filter(is_active=True)

    @cache_public_data(redis_client=restaurants_public_cache)
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


@extend_schema_view(
    get=extend_schema(
        tags=['Public Restaurants'],
        summary='Детальна інформація про ресторан',
        description='Отримати детальну інформацію про конкретний активний ресторан за його унікальним slug. Результат кешується.'
    )
)
class RestaurantDetailView(generics.RetrieveAPIView):
    """
        Повертає повну інформацію про один ресторан для сторінки закладу в додатку.
        Пошук відбувається по полю slug.
    """
    queryset = Restaurant.objects.filter(is_active=True)
    serializer_class = RestaurantSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'

    @cache_public_data(redis_client=restaurants_public_cache)
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
