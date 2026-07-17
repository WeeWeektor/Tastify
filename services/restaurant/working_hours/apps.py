from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class WorkingHoursConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'working_hours'
    verbose_name = _("Working Hours")
