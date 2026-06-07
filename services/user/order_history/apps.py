from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class OrderHistoryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'order_history'
    verbose_name = _('Order History')
