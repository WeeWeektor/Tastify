from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from shared.decorators.cache_public_data_decorator import invalidate_public_data_cache
from .models import Restaurant
from .services import restaurants_public_cache


@receiver(post_save, sender=Restaurant)
@receiver(post_delete, sender=Restaurant)
def invalidate_restaurant_cache(sender, instance, **kwargs):
    """
        Сигнал, який автоматично очищає кеш при будь-якій зміні в моделі Restaurant.
        Спрацьовує при оновленні через API, Celery Beat або Django Admin.
    """
    detail_path = f"/api/v1/restaurants/{instance.slug}/"
    invalidate_public_data_cache(restaurants_public_cache, detail_path)

    list_path = "/api/v1/restaurants/"
    invalidate_public_data_cache(restaurants_public_cache, list_path)
