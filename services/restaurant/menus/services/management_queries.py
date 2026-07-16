from django.db.models import QuerySet
from django.shortcuts import get_object_or_404

from menus.models import Product, MenuCategory, MenuItem, ModifierGroup, ModifierOption
from restaurants.models import Restaurant


def get_management_products_qs(restaurant_slug: str) -> QuerySet[Product]:
    return Product.objects.filter(restaurant__slug=restaurant_slug)


def get_management_categories_qs(restaurant_slug: str) -> QuerySet[MenuCategory]:
    return MenuCategory.objects.filter(restaurant__slug=restaurant_slug)


def get_management_menu_items_qs(restaurant_slug: str) -> QuerySet[MenuItem]:
    return MenuItem.objects.filter(category__restaurant__slug=restaurant_slug)


def get_management_modifier_groups_qs(restaurant_slug: str, item_id: str = None) -> QuerySet[ModifierGroup]:
    qs = ModifierGroup.objects.filter(menu_item__category__restaurant__slug=restaurant_slug)
    if item_id:
        qs = qs.filter(menu_item_id=item_id)
    return qs


def get_management_modifier_options_qs(restaurant_slug: str, group_id: str = None) -> QuerySet[ModifierOption]:
    qs = ModifierOption.objects.filter(group__menu_item__category__restaurant__slug=restaurant_slug)
    if group_id:
        qs = qs.filter(group_id=group_id)
    return qs


def get_restaurant_for_management(restaurant_slug: str) -> Restaurant:
    return get_object_or_404(Restaurant, slug=restaurant_slug)


def get_category_for_management(category_id: str, restaurant_slug: str) -> MenuCategory:
    return get_object_or_404(MenuCategory, id=category_id, restaurant__slug=restaurant_slug)


def get_menu_item_for_management(item_id: str, restaurant_slug: str) -> MenuItem:
    return get_object_or_404(MenuItem, id=item_id, category__restaurant__slug=restaurant_slug)


def get_modifier_group_for_management(group_id: str, restaurant_slug: str) -> ModifierGroup:
    return get_object_or_404(ModifierGroup, id=group_id, menu_item__category__restaurant__slug=restaurant_slug)
