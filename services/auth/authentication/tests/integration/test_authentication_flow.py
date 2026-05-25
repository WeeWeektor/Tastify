from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()


@pytest.mark.django_db
class TestCoreAuthenticationFlow:
    """
    Інтеграційний тест повного життєвого циклу користувача:
    Реєстрація -> Відмова в логіні (непідтверджений) -> Верифікація -> Успішний логін -> Логаут.
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

    @patch('authentication.services.email_service.send_mail')
    def test_full_user_lifecycle(self, mock_send_mail, api_client):
        register_url = '/api/v1/auth/register/'
        register_data = {
            'email': 'integration@test.com',
            'password': 'StrongPassword123!',
            'password_confirm': 'StrongPassword123!'
        }

        response = api_client.post(register_url, register_data)
        assert response.status_code == status.HTTP_201_CREATED

        user = User.objects.get(email='integration@test.com')
        assert user.is_verified is False

        mock_send_mail.assert_called_once()

        login_url = '/api/v1/auth/login/'
        login_data = {
            'email': 'integration@test.com',
            'password': 'StrongPassword123!'
        }

        response = api_client.post(login_url, login_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Please confirm your email" in response.data['detail']

        email_message = mock_send_mail.call_args.kwargs['message']

        import re
        token_match = re.search(r'token=([a-f0-9\-]+)', email_message)
        assert token_match is not None, "Token not found in email body"
        verification_token = token_match.group(1)

        verify_url = f'/api/v1/auth/verify-email/?token={verification_token}'
        response = api_client.get(verify_url)

        assert response.status_code == status.HTTP_200_OK

        user.refresh_from_db()
        assert user.is_verified is True

        response = api_client.post(login_url, login_data)

        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data

        access_token = response.data['access']
        refresh_token = response.data['refresh']

        logout_url = '/api/v1/auth/logout/'

        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        response = api_client.post(logout_url, {'refresh': refresh_token})
        assert response.status_code == status.HTTP_204_NO_CONTENT

        response = api_client.post(logout_url, {'refresh': refresh_token})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already been blocked" in str(response.data)
