from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class RestaurantsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'restaurants'
    verbose_name = _("Restaurants Management")

    def ready(self):
        """
        Цей метод викликається один раз при старті додатку.
        Тут ми імпортуємо сигнали, щоб вони підключилися до моделей.
        """
        import restaurants.signals
