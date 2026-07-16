from django.db.models import Prefetch, QuerySet

from menus.models import MenuCategory, MenuItem, ModifierGroup, ModifierOption


def get_public_menu_items_queryset(restaurant_slug: str = None) -> QuerySet[MenuItem]:
    """
        Будує оптимізований запит для отримання активних страв
        з усіма підключеними модифікаторами та продуктами.
    """
    active_options = ModifierOption.objects.filter(is_available=True).order_by('order')

    active_groups = ModifierGroup.objects.prefetch_related(
        Prefetch('options', queryset=active_options)
    ).order_by('order')

    qs = MenuItem.objects.select_related('base_product').filter(
        is_active=True,
        is_available=True
    ).prefetch_related(
        Prefetch('modifier_groups', queryset=active_groups)
    )

    if restaurant_slug:
        qs = qs.filter(category__restaurant__slug=restaurant_slug)

    return qs


def get_public_categories_queryset(restaurant_slug: str) -> QuerySet[MenuCategory]:
    """
    Будує запит для отримання всього дерева меню ресторану.
    """
    active_items = get_public_menu_items_queryset().order_by('name')

    return MenuCategory.objects.filter(
        restaurant__slug=restaurant_slug,
        is_active=True
    ).prefetch_related(
        Prefetch('items', queryset=active_items)
    ).order_by('order')
