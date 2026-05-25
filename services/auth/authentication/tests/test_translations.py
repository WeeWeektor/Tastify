import pytest
from django.utils import translation
from django.utils.translation import gettext as _
from rest_framework.test import APIClient
from django.conf import settings


@pytest.mark.django_db
class TestTranslationSuite:
    """
    Комплексний набір тестів для перевірки інтернаціоналізації.
    """

    def test_engine_translation(self):
        """Перевірка, чи працює переклад на рівні коду."""
        translation.activate('uk')
        assert _("Incorrect email address or password.") == "Неправильна email адреса або пароль."
        translation.deactivate()

    def test_api_language_switching(self):
        """Перевірка API заголовків (Accept-Language)."""
        client = APIClient()

        client.defaults['HTTP_ACCEPT_LANGUAGE'] = 'uk'
        response_uk = client.post('/api/v1/auth/login/', data={'email': 'x@x.com', 'password': 'y'})
        assert "Неправильна" in str(response_uk.data['detail'])

        client.defaults['HTTP_ACCEPT_LANGUAGE'] = 'en'
        response_en = client.post('/api/v1/auth/login/', data={'email': 'x@x.com', 'password': 'y'})
        assert "Incorrect" in str(response_en.data['detail'])

    def test_config_paths(self):
        """Перевірка, чи Django бачить папку з перекладами."""
        expected_path = str(settings.BASE_DIR / 'locale')
        assert any(expected_path in p for p in settings.LOCALE_PATHS), \
            f"Шлях {expected_path} не знайдено в LOCALE_PATHS. Поточні: {settings.LOCALE_PATHS}"