import pyotp
import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()


@pytest.mark.django_db
class TestTwoFactorIntegrationFlow:
    """
    Інтеграційний тест повного життєвого циклу 2FA:
    Логін -> Налаштування 2FA -> Увімкнення 2FA -> Логаут ->
    Новий логін (видає pre_auth_token) -> Введення коду -> Фінальний JWT.
    """

    @pytest.fixture(autouse=True)
    def clear_cache(self):
        """Очищення кешу для коректної роботи Rate Limits."""
        cache.clear()
        yield
        cache.clear()

    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.fixture
    def active_user(self):
        """Створюємо верифікованого користувача для тесту."""
        return User.objects.create_user(
            email='secure@test.com',
            password='StrongPassword123!',
            is_verified=True,
            is_active=True
        )

    def test_full_2fa_lifecycle(self, api_client, active_user):
        login_url = '/api/v1/auth/login/'
        login_data = {
            'email': 'secure@test.com',
            'password': 'StrongPassword123!'
        }

        response = api_client.post(login_url, login_data)
        assert response.status_code == status.HTTP_200_OK

        assert 'access' in response.data
        access_token = response.data['access']

        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        setup_2fa_url = '/api/v1/auth/2fa/setup/'

        response = api_client.post(setup_2fa_url)
        assert response.status_code == status.HTTP_200_OK

        assert 'secret' in response.data
        totp_secret = response.data['secret']

        enable_2fa_url = '/api/v1/auth/2fa/enable/'

        totp = pyotp.TOTP(totp_secret)
        valid_code = totp.now()

        response = api_client.post(enable_2fa_url, {'code': valid_code})
        assert response.status_code == status.HTTP_200_OK

        active_user.refresh_from_db()
        assert active_user.is_2fa_enabled is True

        api_client.credentials()

        response = api_client.post(login_url, login_data)
        assert response.status_code == status.HTTP_200_OK

        assert response.data.get('requires_2fa') is True
        assert 'pre_auth_token' in response.data
        assert 'access' not in response.data

        pre_auth_token = response.data['pre_auth_token']

        verify_2fa_url = '/api/v1/auth/2fa/verify/'

        new_valid_code = pyotp.TOTP(active_user.totp_secret).now()

        verify_data = {
            'pre_auth_token': pre_auth_token,
            'code': new_valid_code
        }

        response = api_client.post(verify_2fa_url, verify_data)
        assert response.status_code == status.HTTP_200_OK

        assert 'access' in response.data
        assert 'refresh' in response.data
