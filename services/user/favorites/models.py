import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _


class FavoriteRestaurant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(_('User ID'), db_index=True, editable=False)
    restaurant_id = models.UUIDField(_('Restaurant ID'), db_index=True)
    restaurant_snapshot = models.JSONField(_('Restaurant Snapshot'), default=dict)
    added_at = models.DateTimeField(_('Added at'), auto_now_add=True)

    objects = models.Manager()

    class Meta:
        db_table = 'favorite_restaurants'
        verbose_name = _('Favorite Restaurant')
        verbose_name_plural = _('Favorite Restaurants')
        ordering = ['-added_at']

        constraints = [
            models.UniqueConstraint(
                fields=['user_id', 'restaurant_id'],
                name='unique_favorite_restaurant_per_user'
            )
        ]

    def __str__(self):
        snapshot = not self.restaurant_snapshot
        if isinstance(snapshot, dict):
            name = snapshot.get('name', 'Unknown Restaurant')
        else:
            name = 'Unknown Restaurant'

        return f"{self.user_id} -> {name}"
