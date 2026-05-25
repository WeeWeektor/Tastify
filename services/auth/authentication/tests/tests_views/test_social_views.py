from unittest.mock import patch

import pytest
from django.core.cache import cache
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.test import APIClient


@pytest.mark.django_db
class TestSocialAuthViews:

    @pytest.fixture(autouse=True)
    def clear_cache(self):
        """Очищує кеш для скидання лімітів AdvancedRateLimitMiddleware."""
        cache.clear()
        yield
        cache.clear()

    @pytest.fixture
    def api_client(self):
        return APIClient()

    @patch('authentication.views.social.SocialAuthService.get_google_auth_url')
    def test_google_oauth_view_redirects_to_google(self, mock_get_url, api_client):
        """Перевірка, що ендпоінт перенаправляє користувача на сторінку логіну Google."""
        fake_google_url = "https://accounts.google.com/o/oauth2/v2/auth?client_id=123"
        mock_get_url.return_value = fake_google_url

        url = '/api/v1/auth/social/google/'

        response = api_client.get(url)

        assert response.status_code == status.HTTP_302_FOUND
        assert response.url == fake_google_url

        mock_get_url.assert_called_once()

    @patch('authentication.views.social.SocialAuthService.process_google_callback')
    def test_google_oauth_callback_success(self, mock_process_callback, api_client, settings):
        """Успішна авторизація повертає редирект на фронтенд з токенами в URL."""
        settings.FRONTEND_URL = "https://tastify.com"

        mock_process_callback.return_value = {
            'access': 'fake-access-token',
            'refresh': 'fake-refresh-token'
        }

        url = '/api/v1/auth/social/google/callback/'

        response = api_client.get(url, {'code': 'google-auth-code'})

        assert response.status_code == status.HTTP_302_FOUND

        expected_redirect_url = "https://tastify.com/oauth/callback?access=fake-access-token&refresh=fake-refresh-token"
        assert response.url == expected_redirect_url

        mock_process_callback.assert_called_once()

    @patch('authentication.views.social.SocialAuthService.process_google_callback')
    def test_google_oauth_callback_failure(self, mock_process_callback, api_client):
        """Якщо Google відмовив в авторизації, View має повернути 401."""
        mock_process_callback.side_effect = AuthenticationFailed("User is disabled or not found.")

        url = '/api/v1/auth/social/google/callback/'
        response = api_client.get(url, {'error': 'access_denied'})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "User is disabled or not found" in response.data['detail']
