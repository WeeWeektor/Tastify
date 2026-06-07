import uuid

from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _


class OrderHistoryItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_id = models.UUIDField(_('Original Order ID'), unique=True)
    user_id = models.UUIDField(_('User ID'), db_index=True)
    restaurant_id = models.UUIDField(_('Restaurant ID'))
    restaurant_name = models.CharField(_('Restaurant Name'), max_length=200)
    restaurant_logo = models.URLField(_('Restaurant Logo URL'), null=True, blank=True)
    total_amount = models.DecimalField(_('Total Amount'), max_digits=10, decimal_places=2)
    items_summary = models.JSONField(_('Items Summary'), default=list)
    status = models.CharField(_('Status'), max_length=50)
    delivery_address_short = models.CharField(
        _('Short Delivery Address'),
        max_length=255,
        blank=True,
        default='',
        help_text=_("Short address for the list (e.g. '22 Khreshchatyk Street')")
    )
    rating_given = models.SmallIntegerField(_('Rating Given'), null=True, blank=True)
    created_at = models.DateTimeField(_('Created At'))
    delivered_at = models.DateTimeField(_('Delivered At'), null=True, blank=True)

    objects = models.Manager()

    class Meta:
        db_table = 'order_history_items'
        verbose_name = _('Order History Item')
        verbose_name_plural = _('Order History Items')
        ordering = ['-created_at']

        indexes = [
            models.Index(fields=['user_id', '-created_at'], name='idx_user_history'),
        ]
        constraints = [
            models.CheckConstraint(
                check=Q(rating_given__gte=1) & Q(rating_given__lte=5),
                name='check_rating_range'
            )
        ]

    def __str__(self):
        return f"Order {self.order_id} - {self.status}"
