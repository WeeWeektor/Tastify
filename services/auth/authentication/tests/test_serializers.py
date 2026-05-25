from datetime import timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.tokens import RefreshToken

from authentication.mixins import PasswordValidationAndConfirmationMixin
from authentication.models import RefreshTokenBlacklist
from authentication.serializers import CustomTokenRefreshSerializer

User = get_user_model()


class TestPasswordValidationMixin:

    def test_valid_passwords_match(self):
        """Сценарій 1: Паролі співпадають і відповідають вимогам."""
        data = {
            'password': 'StrongPassword123!',
            'password_confirm': 'StrongPassword123!'
        }
        serializer = PasswordValidationAndConfirmationMixin(data=data)

        assert serializer.is_valid() is True
        assert serializer.validated_data['password'] == 'StrongPassword123!'

    def test_invalid_passwords_do_not_match(self):
        """Сценарій 2: Паролі не співпадають."""
        data = {
            'password': 'StrongPassword123!',
            'password_confirm': 'DifferentPassword321!'
        }
        serializer = PasswordValidationAndConfirmationMixin(data=data)

        assert serializer.is_valid() is False
        assert 'password_confirm' in serializer.errors
        assert serializer.errors['password_confirm'][0].code == 'invalid'
        assert str(serializer.errors['password_confirm'][0]) == 'Passwords do not match.'

    def test_invalid_password_too_short(self):
        """Сценарій 3: Пароль коротший за 8 символів."""
        data = {
            'password': 'short',
            'password_confirm': 'short'
        }
        serializer = PasswordValidationAndConfirmationMixin(data=data)

        assert serializer.is_valid() is False
        assert 'password' in serializer.errors
        assert serializer.errors['password'][0].code == 'min_length'

    def test_missing_password_fields(self):
        """Сценарій 4: Поля не передані взагалі."""
        data = {}
        serializer = PasswordValidationAndConfirmationMixin(data=data)

        assert serializer.is_valid() is False
        assert 'password' in serializer.errors
        assert 'password_confirm' in serializer.errors
        assert serializer.errors['password'][0].code == 'required'
        assert serializer.errors['password_confirm'][0].code == 'required'

    def test_blank_password_fields(self):
        """Сценарій 5: Передані порожні рядки."""
        data = {
            'password': '',
            'password_confirm': ''
        }
        serializer = PasswordValidationAndConfirmationMixin(data=data)

        assert serializer.is_valid() is False
        assert 'password' in serializer.errors
        assert 'password_confirm' in serializer.errors
        assert serializer.errors['password'][0].code == 'blank'
        assert serializer.errors['password_confirm'][0].code == 'blank'


@pytest.mark.django_db
class TestCustomTokenRefreshSerializer:

    @pytest.fixture
    def user(self):
        """Створюємо тестового користувача."""
        user = User.objects.create_user(
            email='refresh_test@example.com',
            password='Password123!'
        )
        user.last_login = timezone.now() - timedelta(minutes=10)
        user.save()
        return user

    @pytest.fixture
    def valid_refresh_token(self, user):
        return RefreshToken.for_user(user)

    @patch('authentication.serializers.token_blacklist_service.get_value')
    def test_refresh_token_success(self, mock_get_value, valid_refresh_token):
        """Сценарій 1: Токен валідний, не в чорному списку, юзер існує."""
        mock_get_value.return_value = None

        serializer = CustomTokenRefreshSerializer(data={'refresh': str(valid_refresh_token)})

        assert serializer.is_valid() is True
        assert 'access' in serializer.validated_data

    @patch('authentication.serializers.token_blacklist_service.get_value')
    def test_refresh_token_blacklisted_in_redis(self, mock_get_value, valid_refresh_token):
        """Сценарій 2: Токен знайдено в Redis."""
        mock_get_value.return_value = "blacklisted"

        serializer = CustomTokenRefreshSerializer(data={'refresh': str(valid_refresh_token)})

        with pytest.raises(InvalidToken, match="This token has been blacklisted."):
            serializer.is_valid(raise_exception=True)

    @patch('authentication.serializers.token_blacklist_service.get_value')
    def test_refresh_token_blacklisted_in_db(self, mock_get_value, user, valid_refresh_token):
        """Сценарій 3: Токен знайдено в Базі Даних (RefreshTokenBlacklist)."""
        mock_get_value.return_value = None

        RefreshTokenBlacklist.objects.create(
            jti=valid_refresh_token['jti'],
            user_id=user.id,
            expires_at=timezone.now() + timedelta(days=1)
        )

        serializer = CustomTokenRefreshSerializer(data={'refresh': str(valid_refresh_token)})

        with pytest.raises(InvalidToken, match="This token has been blacklisted."):
            serializer.is_valid(raise_exception=True)

    @patch('authentication.serializers.token_blacklist_service.get_value')
    def test_refresh_token_user_not_found(self, mock_get_value, user, valid_refresh_token):
        """Сценарій 4: Юзера було видалено після випуску токена."""
        mock_get_value.return_value = None

        user.delete()

        serializer = CustomTokenRefreshSerializer(data={'refresh': str(valid_refresh_token)})

        with pytest.raises(InvalidToken, match="User not found."):
            serializer.is_valid(raise_exception=True)

    @patch('authentication.serializers.token_blacklist_service.get_value')
    def test_refresh_token_password_changed(self, mock_get_value, user, valid_refresh_token):
        """
        Сценарій 5: Пароль змінено (або логаут).
        last_login оновлено після випуску токена.
        """
        mock_get_value.return_value = None

        user.last_login = timezone.now() + timedelta(minutes=5)
        user.save()

        serializer = CustomTokenRefreshSerializer(data={'refresh': str(valid_refresh_token)})

        with pytest.raises(InvalidToken, match="Password was changed. Please log in again."):
            serializer.is_valid(raise_exception=True)
