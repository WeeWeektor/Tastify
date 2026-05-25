from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

User = get_user_model()


@pytest.mark.django_db
class TestAuthenticationViews:

    @pytest.fixture(autouse=True)
    def clear_cache(self):
        """
        Очищує кеш перед кожним тестом.
        Це скидає лічильники AdvancedRateLimitMiddleware,
        щоб тести не отримували помилку 429 (Too Many Requests).
        """
        cache.clear()
        yield
        cache.clear()

    @pytest.fixture
    def api_client(self):
        """Клієнт для симуляції HTTP-запитів."""
        return APIClient()

    @pytest.fixture
    def active_user(self):
        """Звичайний активний користувач для тестів, де потрібна авторизація."""
        return User.objects.create_user(
            email='user@example.com',
            password='StrongPassword123!',
            is_active=True
        )

    @patch('authentication.views.auth.AuthenticationService.register')
    def test_register_view_success(self, mock_register, api_client):
        """Успішна реєстрація повертає 201 Created."""
        url = reverse('register')
        data = {
            'email': 'new@example.com',
            'password': 'StrongPassword123!',
            'password_confirm': 'StrongPassword123!'
        }

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert "User registered successfully" in response.data['message']
        mock_register.assert_called_once_with(
            email='new@example.com',
            password='StrongPassword123!',
            role='customer'
        )

    def test_register_view_invalid_data(self, api_client):
        """Помилка 400, якщо серіалізатор не пропустив дані (наприклад, різні паролі)."""
        url = reverse('register')
        data = {
            'email': 'bad@example.com',
            'password': 'Password123!',
            'password_confirm': 'DifferentPassword321!'
        }

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password_confirm' in response.data

    @patch('authentication.views.auth.AuthenticationService.verify_email')
    def test_verify_email_view_success(self, mock_verify, api_client):
        """Успішне підтвердження пошти (200 OK)."""
        url = reverse('verify-email')

        response = api_client.get(url, {'token': 'valid-token'})

        assert response.status_code == status.HTTP_200_OK
        mock_verify.assert_called_once_with('valid-token')

    def test_verify_email_view_missing_token(self, api_client):
        """Помилка 400, якщо токен не передано в query параметрах."""
        url = reverse('verify-email')

        response = api_client.get(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Token is required" in response.data['error']

    @patch('authentication.views.auth.AuthenticationService.verify_email')
    def test_verify_email_view_invalid_token(self, mock_verify, api_client):
        """Якщо сервіс кидає ValidationError, View має повернути 400."""
        mock_verify.side_effect = ValidationError({"token": "Invalid token."})
        url = reverse('verify-email')

        response = api_client.get(url, {'token': 'bad-token'})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'token' in response.data

    @patch('authentication.views.auth.AuthenticationService.login')
    def test_login_view_success_standard(self, mock_login, api_client):
        """Стандартний успішний логін видає access та refresh токени."""
        url = reverse('login')
        data = {'email': 'test@example.com', 'password': 'Password123!'}

        mock_login.return_value = {
            "requires_2fa": False,
            "pre_auth_token": None,
            "refresh": "fake-refresh-token",
            "access": "fake-access-token"
        }

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['access'] == "fake-access-token"
        assert response.data['refresh'] == "fake-refresh-token"
        assert 'requires_2fa' not in response.data

    @patch('authentication.views.auth.AuthenticationService.login')
    def test_login_view_requires_2fa(self, mock_login, api_client):
        """Логін юзера з увімкненою 2FA видає pre_auth_token замість JWT."""
        url = reverse('login')
        data = {'email': 'test@example.com', 'password': 'Password123!'}

        mock_login.return_value = {
            "requires_2fa": True,
            "pre_auth_token": "uuid-pre-auth",
            "refresh": None,
            "access": None
        }

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['requires_2fa'] is True
        assert response.data['pre_auth_token'] == "uuid-pre-auth"
        assert 'access' not in response.data

    @patch('authentication.views.auth.AuthenticationService.logout')
    def test_logout_view_success(self, mock_logout, api_client, active_user):
        """Успішний логаут авторизованого користувача (204 No Content)."""
        url = reverse('logout')

        api_client.force_authenticate(user=active_user)

        data = {'refresh': 'valid-refresh-token'}
        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        mock_logout.assert_called_once_with('valid-refresh-token')

    def test_logout_view_unauthenticated(self, api_client):
        """Якщо юзер не авторизований, його не пускає до LogoutView (401)."""
        url = reverse('logout')

        response = api_client.post(url, {'refresh': 'some-token'})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_logout_view_missing_token(self, api_client, active_user):
        """Помилка 400, якщо не передати refresh токен у тілі запиту."""
        url = reverse('logout')
        api_client.force_authenticate(user=active_user)

        response = api_client.post(url, {})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'refresh' in response.data

    def test_token_refresh_view_invalid_token(self, api_client):
        """Перевірка, що ендпоінт налаштований і відповідає 401 на биті токени."""
        url = reverse('token_refresh')

        response = api_client.post(url, {'refresh': 'fake-or-expired-token'})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
