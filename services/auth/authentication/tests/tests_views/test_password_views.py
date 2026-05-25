from unittest.mock import patch

import pytest
from django.core.cache import cache
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient


@pytest.mark.django_db
class TestPasswordManagementViews:

    @pytest.fixture(autouse=True)
    def clear_cache(self):
        """Очищує кеш перед кожним тестом для скидання лімітів (Rate Limit)."""
        cache.clear()
        yield
        cache.clear()

    @pytest.fixture
    def api_client(self):
        return APIClient()

    @patch('authentication.views.password.PasswordService.request_password_reset')
    def test_password_reset_request_success(self, mock_request_reset, api_client):
        """Успішний запит на скидання пароля повертає 200 OK."""
        url = '/api/v1/auth/password/reset/'
        data = {'email': 'user@example.com'}

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert "password reset link has been sent" in response.data['message']

        mock_request_reset.assert_called_once_with('user@example.com')

    def test_password_reset_request_invalid_email(self, api_client):
        """Помилка 400, якщо передати невалідний email."""
        url = '/api/v1/auth/password/reset/'
        data = {'email': 'not-an-email'}

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'email' in response.data

    def test_password_reset_request_missing_email(self, api_client):
        """Помилка 400, якщо email взагалі не передано."""
        url = '/api/v1/auth/password/reset/'

        response = api_client.post(url, {})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'email' in response.data

    @patch('authentication.views.password.PasswordService.confirm_password_reset')
    def test_password_reset_confirm_success(self, mock_confirm_reset, api_client):
        """Успішне встановлення нового пароля повертає 200 OK."""
        url = '/api/v1/auth/password/reset/confirm/'
        data = {
            'token': 'valid-uuid-token',
            'password': 'NewStrongPassword123!',
            'password_confirm': 'NewStrongPassword123!'
        }

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert "password has been successfully reset" in response.data['message']

        mock_confirm_reset.assert_called_once_with(
            token='valid-uuid-token',
            new_password='NewStrongPassword123!'
        )

    def test_password_reset_confirm_passwords_mismatch(self, api_client):
        """Помилка 400, якщо паролі не співпадають (відловлює серіалізатор)."""
        url = '/api/v1/auth/password/reset/confirm/'
        data = {
            'token': 'valid-uuid-token',
            'password': 'NewStrongPassword123!',
            'password_confirm': 'DifferentPassword321!'
        }

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password_confirm' in response.data

    @patch('authentication.views.password.PasswordService.confirm_password_reset')
    def test_password_reset_confirm_invalid_token(self, mock_confirm_reset, api_client):
        """Якщо сервіс відхиляє токен (ValidationError), View має повернути 400."""
        mock_confirm_reset.side_effect = ValidationError({"token": "The token is invalid or has expired."})

        url = '/api/v1/auth/password/reset/confirm/'
        data = {
            'token': 'invalid-or-expired-token',
            'password': 'NewStrongPassword123!',
            'password_confirm': 'NewStrongPassword123!'
        }

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'token' in response.data
