import re
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()


@pytest.mark.django_db
class TestPasswordResetIntegrationFlow:
    """
    Інтеграційний тест повного життєвого циклу скидання пароля:
    Запит на скидання -> Отримання листа -> Витягування токена ->
    Встановлення нового пароля -> Успішний логін з новим паролем.
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
        """Створюємо верифікованого користувача зі старим паролем."""
        return User.objects.create_user(
            email='forgetful@test.com',
            password='OldPassword123!',
            is_verified=True,
            is_active=True
        )

    @patch('authentication.services.email_service.send_mail')
    def test_full_password_reset_lifecycle(self, mock_send_mail, api_client, active_user):
        request_reset_url = '/api/v1/auth/password/reset/'

        response = api_client.post(request_reset_url, {'email': 'forgetful@test.com'})
        assert response.status_code == status.HTTP_200_OK

        mock_send_mail.assert_called_once()

        email_message = mock_send_mail.call_args.kwargs['message']

        token_match = re.search(r'token=([a-f0-9\-]+)', email_message)
        assert token_match is not None, "Reset token not found in email body"
        reset_token = token_match.group(1)

        confirm_reset_url = '/api/v1/auth/password/reset/confirm/'
        new_password = 'BrandNewPassword999!'

        confirm_data = {
            'token': reset_token,
            'password': new_password,
            'password_confirm': new_password
        }

        response = api_client.post(confirm_reset_url, confirm_data)
        assert response.status_code == status.HTTP_200_OK
        assert "password has been successfully reset" in str(response.data)

        response_retry = api_client.post(confirm_reset_url, confirm_data)
        assert response_retry.status_code == status.HTTP_400_BAD_REQUEST

        login_url = '/api/v1/auth/login/'

        bad_login_response = api_client.post(login_url, {
            'email': 'forgetful@test.com',
            'password': 'OldPassword123!'
        })
        assert bad_login_response.status_code == status.HTTP_400_BAD_REQUEST

        good_login_response = api_client.post(login_url, {
            'email': 'forgetful@test.com',
            'password': new_password
        })
        assert good_login_response.status_code == status.HTTP_200_OK
        assert 'access' in good_login_response.data
        assert 'refresh' in good_login_response.data
