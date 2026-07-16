from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from menus.mixins import MenuCacheInvalidationMixin
from menus.serializers.management_serializers import (
    ManagementProductSerializer,
    ManagementMenuCategorySerializer,
    ManagementMenuItemSerializer,
    ManagementModifierGroupSerializer,
    ManagementModifierOptionSerializer
)
from menus.services.management_queries import (
    get_management_products_qs, get_restaurant_for_management,
    get_management_categories_qs,
    get_management_menu_items_qs, get_category_for_management,
    get_management_modifier_groups_qs, get_menu_item_for_management,
    get_management_modifier_options_qs, get_modifier_group_for_management
)
from restaurants.permissions import IsMenuEditor


@extend_schema_view(
    get=extend_schema(
        tags=['Management: Products'],
        summary='Список базових продуктів',
        description='Отримати список усіх базових продуктів (складських позицій) ресторану.'
    ),
    post=extend_schema(
        tags=['Management: Products'],
        summary='Створити базовий продукт',
        description='Створює новий базовий продукт. Зверніть увагу: створення продукту не впливає на кеш публічного меню напряму.'
    )
)
class ManagementProductListCreateView(generics.ListCreateAPIView):
    serializer_class = ManagementProductSerializer
    permission_classes = [IsAuthenticated, IsMenuEditor]

    def get_queryset(self):
        return get_management_products_qs(self.kwargs['restaurant_slug'])

    def perform_create(self, serializer):
        restaurant = get_restaurant_for_management(self.kwargs['restaurant_slug'])
        serializer.save(restaurant=restaurant)


@extend_schema_view(
    get=extend_schema(tags=['Management: Products'], summary='Деталі базового продукту'),
    put=extend_schema(tags=['Management: Products'], summary='Повне оновлення продукту'),
    patch=extend_schema(tags=['Management: Products'], summary='Часткове оновлення продукту'),
    delete=extend_schema(
        tags=['Management: Products'],
        summary='Видалити продукт',
        description='Видаляє продукт. Рекомендується використовувати м\'яке видалення (is_active=False) замість фізичного, якщо продукт вже використовувався у стравах.'
    )
)
class ManagementProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ManagementProductSerializer
    permission_classes = [IsAuthenticated, IsMenuEditor]

    def get_queryset(self):
        return get_management_products_qs(self.kwargs['restaurant_slug'])


@extend_schema_view(
    get=extend_schema(
        tags=['Management: Categories'],
        summary='Список категорій меню'
    ),
    post=extend_schema(
        tags=['Management: Categories'],
        summary='Створити категорію',
        description='Створює нову категорію. Автоматично інвалідує публічний кеш списку меню.'
    )
)
class ManagementCategoryListCreateView(generics.ListCreateAPIView, MenuCacheInvalidationMixin):
    serializer_class = ManagementMenuCategorySerializer
    permission_classes = [IsAuthenticated, IsMenuEditor]

    def get_queryset(self):
        return get_management_categories_qs(self.kwargs['restaurant_slug'])

    def perform_create(self, serializer):
        restaurant = get_restaurant_for_management(self.kwargs['restaurant_slug'])
        serializer.save(restaurant=restaurant)
        self.invalidate_menu_cache(self.kwargs['restaurant_slug'])


@extend_schema_view(
    get=extend_schema(tags=['Management: Categories'], summary='Деталі категорії'),
    put=extend_schema(tags=['Management: Categories'], summary='Оновити категорію (очищує кеш)'),
    patch=extend_schema(tags=['Management: Categories'], summary='Частково оновити категорію (очищує кеш)'),
    delete=extend_schema(
        tags=['Management: Categories'],
        summary='Видалити категорію (очищує кеш)',
        description='УВАГА: Видалення категорії каскадно видалить усі страви всередині неї!'
    )
)
class ManagementCategoryDetailView(generics.RetrieveUpdateDestroyAPIView, MenuCacheInvalidationMixin):
    serializer_class = ManagementMenuCategorySerializer
    permission_classes = [IsAuthenticated, IsMenuEditor]

    def get_queryset(self):
        return get_management_categories_qs(self.kwargs['restaurant_slug'])

    def perform_update(self, serializer):
        super().perform_update(serializer)
        self.invalidate_menu_cache(self.kwargs['restaurant_slug'])

    def perform_destroy(self, instance):
        super().perform_destroy(instance)
        self.invalidate_menu_cache(self.kwargs['restaurant_slug'])


@extend_schema_view(
    get=extend_schema(
        tags=['Management: Menu Items'],
        summary='Список страв ресторану'
    ),
    post=extend_schema(
        tags=['Management: Menu Items'],
        summary='Додати нову страву',
        description='Створює страву. Категорія (category_id) передається в тілі запиту та перевіряється на приналежність до ресторану. Кеш очищується.'
    )
)
class ManagementMenuItemListCreateView(generics.ListCreateAPIView, MenuCacheInvalidationMixin):
    serializer_class = ManagementMenuItemSerializer
    permission_classes = [IsAuthenticated, IsMenuEditor]

    def get_queryset(self):
        return get_management_menu_items_qs(self.kwargs['restaurant_slug'])

    def perform_create(self, serializer):
        category_id = self.request.data.get('category')
        category = get_category_for_management(category_id, self.kwargs['restaurant_slug'])
        item = serializer.save(category=category)
        self.invalidate_menu_cache(self.kwargs['restaurant_slug'], item_id=item.id)


@extend_schema_view(
    get=extend_schema(tags=['Management: Menu Items'], summary='Деталі конкретної страви'),
    put=extend_schema(tags=['Management: Menu Items'], summary='Оновити страву (очищує кеш)'),
    patch=extend_schema(tags=['Management: Menu Items'],
                        summary='Частково оновити страву (напр., змінити ціну) (очищує кеш)'),
    delete=extend_schema(tags=['Management: Menu Items'], summary='Видалити страву (очищує кеш)')
)
class ManagementMenuItemDetailView(generics.RetrieveUpdateDestroyAPIView, MenuCacheInvalidationMixin):
    serializer_class = ManagementMenuItemSerializer
    permission_classes = [IsAuthenticated, IsMenuEditor]

    def get_queryset(self):
        return get_management_menu_items_qs(self.kwargs['restaurant_slug'])

    def perform_update(self, serializer):
        item = serializer.save()
        self.invalidate_menu_cache(self.kwargs['restaurant_slug'], item_id=item.id)

    def perform_destroy(self, instance):
        item_id = instance.id
        super().perform_destroy(instance)
        self.invalidate_menu_cache(self.kwargs['restaurant_slug'], item_id=item_id)


@extend_schema_view(
    get=extend_schema(
        tags=['Management: Modifier Groups'],
        summary='Групи модифікаторів для страви',
        description='Повертає всі групи модифікаторів для конкретної страви.'
    ),
    post=extend_schema(
        tags=['Management: Modifier Groups'],
        summary='Створити групу модифікаторів',
        description='Створює групу (наприклад: "Оберіть соус"). Очищує кеш меню та кеш страви.'
    )
)
class ManagementModifierGroupListCreateView(generics.ListCreateAPIView, MenuCacheInvalidationMixin):
    serializer_class = ManagementModifierGroupSerializer
    permission_classes = [IsAuthenticated, IsMenuEditor]

    def get_queryset(self):
        return get_management_modifier_groups_qs(self.kwargs['restaurant_slug'], self.kwargs['item_id'])

    def perform_create(self, serializer):
        menu_item = get_menu_item_for_management(self.kwargs['item_id'], self.kwargs['restaurant_slug'])
        serializer.save(menu_item=menu_item)
        self.invalidate_menu_cache(self.kwargs['restaurant_slug'], item_id=menu_item.id)


@extend_schema_view(
    get=extend_schema(tags=['Management: Modifier Groups'], summary='Деталі групи модифікаторів'),
    put=extend_schema(tags=['Management: Modifier Groups'], summary='Оновити групу модифікаторів'),
    patch=extend_schema(tags=['Management: Modifier Groups'], summary='Частково оновити групу модифікаторів'),
    delete=extend_schema(tags=['Management: Modifier Groups'], summary='Видалити групу (разом з опціями)')
)
class ManagementModifierGroupDetailView(generics.RetrieveUpdateDestroyAPIView, MenuCacheInvalidationMixin):
    serializer_class = ManagementModifierGroupSerializer
    permission_classes = [IsAuthenticated, IsMenuEditor]

    def get_queryset(self):
        return get_management_modifier_groups_qs(self.kwargs['restaurant_slug'])

    def perform_update(self, serializer):
        group = serializer.save()
        self.invalidate_menu_cache(self.kwargs['restaurant_slug'], item_id=group.menu_item.id)

    def perform_destroy(self, instance):
        item_id = instance.menu_item.id
        super().perform_destroy(instance)
        self.invalidate_menu_cache(self.kwargs['restaurant_slug'], item_id=item_id)


@extend_schema_view(
    get=extend_schema(
        tags=['Management: Modifier Options'],
        summary='Опції для групи модифікаторів'
    ),
    post=extend_schema(
        tags=['Management: Modifier Options'],
        summary='Створити опцію',
        description='Створює конкретну опцію вибору (наприклад: "+ Сир") всередині групи.'
    )
)
class ManagementModifierOptionListCreateView(generics.ListCreateAPIView, MenuCacheInvalidationMixin):
    serializer_class = ManagementModifierOptionSerializer
    permission_classes = [IsAuthenticated, IsMenuEditor]

    def get_queryset(self):
        return get_management_modifier_options_qs(self.kwargs['restaurant_slug'], self.kwargs['group_id'])

    def perform_create(self, serializer):
        group = get_modifier_group_for_management(self.kwargs['group_id'], self.kwargs['restaurant_slug'])
        serializer.save(group=group)
        self.invalidate_menu_cache(self.kwargs['restaurant_slug'], item_id=group.menu_item.id)


@extend_schema_view(
    get=extend_schema(tags=['Management: Modifier Options'], summary='Деталі опції'),
    put=extend_schema(tags=['Management: Modifier Options'], summary='Оновити опцію (напр., ціну)'),
    patch=extend_schema(tags=['Management: Modifier Options'], summary='Частково оновити опцію'),
    delete=extend_schema(tags=['Management: Modifier Options'], summary='Видалити опцію')
)
class ManagementModifierOptionDetailView(generics.RetrieveUpdateDestroyAPIView, MenuCacheInvalidationMixin):
    serializer_class = ManagementModifierOptionSerializer
    permission_classes = [IsAuthenticated, IsMenuEditor]

    def get_queryset(self):
        return get_management_modifier_options_qs(self.kwargs['restaurant_slug'])

    def perform_update(self, serializer):
        option = serializer.save()
        self.invalidate_menu_cache(self.kwargs['restaurant_slug'], item_id=option.group.menu_item.id)

    def perform_destroy(self, instance):
        item_id = instance.group.menu_item.id
        super().perform_destroy(instance)
        self.invalidate_menu_cache(self.kwargs['restaurant_slug'], item_id=item_id)
