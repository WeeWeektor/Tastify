from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

User = get_user_model()


@pytest.mark.django_db
class TestTwoFactorViews:

    @pytest.fixture(autouse=True)
    def clear_cache(self):
        """Очищує кеш для скидання лімітів AdvancedRateLimitMiddleware."""
        cache.clear()
        yield
        cache.clear()

    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.fixture
    def active_user(self):
        return User.objects.create_user(
            email='2fa_user@example.com',
            password='StrongPassword123!',
            is_active=True
        )

    @patch('authentication.views.two_factor.TwoFactorService.generate_totp_secret')
    def test_setup_2fa_success(self, mock_generate, api_client, active_user):
        """Успішне отримання секрету та QR-коду (200 OK)."""
        url = '/api/v1/auth/2fa/setup/'

        mock_generate.return_value = {
            "secret": "JBSWY3DPEHPK3PXP",
            "uri": "otpauth://totp/Tastify:..."
        }

        api_client.force_authenticate(user=active_user)
        response = api_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['secret'] == "JBSWY3DPEHPK3PXP"
        assert 'uri' in response.data

        mock_generate.assert_called_once_with(active_user)

    def test_setup_2fa_unauthenticated(self, api_client):
        """Неавторизований користувач отримує 401 Unauthorized."""
        url = '/api/v1/auth/2fa/setup/'

        response = api_client.post(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @patch('authentication.views.two_factor.TwoFactorService.verify_and_enable')
    def test_enable_2fa_success(self, mock_verify, api_client, active_user):
        """Успішне увімкнення 2FA з правильним кодом."""
        url = '/api/v1/auth/2fa/enable/'

        mock_verify.return_value = True

        api_client.force_authenticate(user=active_user)
        response = api_client.post(url, {'code': '123456'})

        assert response.status_code == status.HTTP_200_OK
        assert "Two-factor authentication enabled successfully" in response.data['detail']

        mock_verify.assert_called_once_with(user=active_user, code='123456')

    @patch('authentication.views.two_factor.TwoFactorService.verify_and_enable')
    def test_enable_2fa_invalid_code(self, mock_verify, api_client, active_user):
        """Якщо код неправильний, сервіс повертає False, а View - помилку 400."""
        url = '/api/v1/auth/2fa/enable/'

        mock_verify.return_value = False

        api_client.force_authenticate(user=active_user)
        response = api_client.post(url, {'code': '000000'})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'code' in response.data

    def test_enable_2fa_bad_payload(self, api_client, active_user):
        """Серіалізатор не пропустить занадто короткий код або його відсутність."""
        url = '/api/v1/auth/2fa/enable/'

        api_client.force_authenticate(user=active_user)
        response = api_client.post(url, {'code': '123'})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'code' in response.data

    def test_enable_2fa_unauthenticated(self, api_client):
        """Неавторизований користувач отримує 401."""
        url = '/api/v1/auth/2fa/enable/'
        response = api_client.post(url, {'code': '123456'})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @patch('authentication.views.two_factor.AuthenticationService.verify_2fa_login')
    def test_verify_2fa_login_success(self, mock_verify_login, api_client):
        """Успішна авторизація через 2FA видає JWT токени."""
        url = '/api/v1/auth/2fa/verify/'
        data = {
            'pre_auth_token': 'valid-uuid-token',
            'code': '123456'
        }

        mock_verify_login.return_value = {
            "refresh": "fake-refresh-token",
            "access": "fake-access-token"
        }

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['access'] == "fake-access-token"
        assert response.data['refresh'] == "fake-refresh-token"

        mock_verify_login.assert_called_once_with(
            pre_auth_token='valid-uuid-token',
            code='123456',
            ip_address='127.0.0.1'
        )

    @patch('authentication.views.two_factor.AuthenticationService.verify_2fa_login')
    def test_verify_2fa_login_invalid_data(self, mock_verify_login, api_client):
        """Якщо сервіс відкидає код або токен, View повертає 400."""
        url = '/api/v1/auth/2fa/verify/'
        data = {
            'pre_auth_token': 'invalid-uuid-token',
            'code': '000000'
        }

        mock_verify_login.side_effect = ValidationError({"code": "Invalid 2FA code."})

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'code' in response.data

    def test_verify_2fa_login_missing_fields(self, api_client):
        """Помилка 400, якщо не передати необхідні поля в запиті."""
        url = '/api/v1/auth/2fa/verify/'

        response = api_client.post(url, {})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'pre_auth_token' in response.data
        assert 'code' in response.data
