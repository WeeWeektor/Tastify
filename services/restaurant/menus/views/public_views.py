from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics
from rest_framework.permissions import AllowAny

from menus.serializers.public_serializers import PublicMenuCategorySerializer, PublicMenuItemSerializer
from menus.services.cache_service import public_menu_list_cache, public_menu_detail_cache
from shared.decorators.cache_public_data_decorator import cache_public_data
from ..services.public_queries import get_public_categories_queryset, get_public_menu_items_queryset


@extend_schema_view(
    get=extend_schema(
        tags=['Public Catalog'],
        summary='Отримати меню ресторану',
        description='Повертає повне дерево меню (категорії -> страви -> модифікатори). '
                    'Виводить тільки активні та доступні позиції.'
    )
)
class PublicMenuListView(generics.ListAPIView):
    serializer_class = PublicMenuCategorySerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        restaurant_slug = self.kwargs.get('slug')
        return get_public_categories_queryset(restaurant_slug)

    @cache_public_data(redis_client=public_menu_list_cache)
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


@extend_schema_view(
    get=extend_schema(
        tags=['Public Catalog'],
        summary='Деталі конкретної страви',
        description='Повертає детальну інформацію про конкретну страву (калорії, інгредієнти) '
                    'разом з її доступними модифікаторами. Доступно лише для активних страв.'
    )
)
class PublicMenuItemDetailView(generics.RetrieveAPIView):
    serializer_class = PublicMenuItemSerializer
    permission_classes = [AllowAny]
    lookup_field = 'id'

    def get_queryset(self):
        restaurant_slug = self.kwargs.get('slug')
        return get_public_menu_items_queryset(restaurant_slug)

    @cache_public_data(redis_client=public_menu_detail_cache)
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
