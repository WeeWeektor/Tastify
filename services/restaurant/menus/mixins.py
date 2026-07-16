from menus.services.cache_service import public_menu_list_cache, public_menu_detail_cache
from shared.decorators.cache_public_data_decorator import invalidate_public_data_cache


class MenuCacheInvalidationMixin:
    """
    Міксін для автоматичного очищення кешу публічного API
    під час створення, оновлення або видалення даних менеджером.
    """

    def invalidate_menu_cache(self, restaurant_slug: str, item_id: str = None):
        list_path = f"/api/v1/restaurants/menus/{restaurant_slug}/"
        invalidate_public_data_cache(public_menu_list_cache, path_prefix=list_path)

        if item_id:
            detail_path = f"/api/v1/restaurants/menus/{restaurant_slug}/items/{item_id}/"
            invalidate_public_data_cache(public_menu_detail_cache, path_prefix=detail_path)
