from unittest.mock import patch, ANY

import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError

from authentication.services.password_service import PasswordService

User = get_user_model()


@pytest.mark.django_db
class TestPasswordService:

    @pytest.fixture
    def active_user(self):
        return User.objects.create_user(
            email='active@example.com',
            password='OldPassword123!',
            is_verified=True,
            is_active=True
        )

    @pytest.fixture
    def unverified_user(self):
        return User.objects.create_user(
            email='unverified@example.com',
            password='OldPassword123!',
            is_verified=False,
            is_active=True
        )

    @pytest.fixture
    def inactive_user(self):
        return User.objects.create_user(
            email='inactive@example.com',
            password='OldPassword123!',
            is_verified=True,
            is_active=False
        )

    @patch('authentication.services.password_service.EmailSenderService.send')
    @patch('authentication.services.password_service.password_reset_service.store')
    def test_request_password_reset_success(self, mock_store, mock_send_email, active_user):
        """Успішний сценарій: юзер існує, активний, лист відправляється."""
        PasswordService.request_password_reset(active_user.email)

        mock_store.assert_called_once_with(value=str(active_user.id), key=ANY)

        mock_send_email.assert_called_once()

        email_template = mock_send_email.call_args[0][0]
        assert email_template.to_email == active_user.email
        assert email_template.reset_token is not None

    @patch('authentication.services.password_service.EmailSenderService.send')
    @patch('authentication.services.password_service.password_reset_service.store')
    def test_request_password_reset_user_not_found(self, mock_store, mock_send_email):
        """Захист від перебору: якщо email не знайдено, сервіс тихо завершує роботу."""
        PasswordService.request_password_reset('doesnotexist@example.com')

        mock_store.assert_not_called()
        mock_send_email.assert_not_called()

    @patch('authentication.services.password_service.EmailSenderService.send')
    @patch('authentication.services.password_service.password_reset_service.store')
    def test_request_password_reset_unverified_user(self, mock_store, mock_send_email, unverified_user):
        """Запит ігнорується, якщо пошта не підтверджена."""
        PasswordService.request_password_reset(unverified_user.email)

        mock_store.assert_not_called()
        mock_send_email.assert_not_called()

    @patch('authentication.services.password_service.EmailSenderService.send')
    @patch('authentication.services.password_service.password_reset_service.store')
    def test_request_password_reset_inactive_user(self, mock_store, mock_send_email, inactive_user):
        """Запит ігнорується, якщо акаунт деактивовано."""
        PasswordService.request_password_reset(inactive_user.email)

        mock_store.assert_not_called()
        mock_send_email.assert_not_called()

    @patch('authentication.services.password_service.password_reset_service.get_value')
    @patch('authentication.services.password_service.password_reset_service.delete')
    def test_confirm_password_reset_success(self, mock_delete, mock_get_value, active_user):
        """Успішне скидання пароля за валідним токеном."""
        fake_token = "valid-reset-token"
        new_password = "NewStrongPassword321!"

        mock_get_value.return_value = str(active_user.id)
        old_last_login = active_user.last_login

        PasswordService.confirm_password_reset(fake_token, new_password)
        active_user.refresh_from_db()

        assert active_user.check_password(new_password) is True
        assert active_user.last_login != old_last_login

        mock_delete.assert_called_once_with(key=fake_token)

    @patch('authentication.services.password_service.password_reset_service.get_value')
    def test_confirm_password_reset_invalid_token(self, mock_get_value):
        """Помилка, якщо токена немає в Redis (протермінований або фейковий)."""
        mock_get_value.return_value = None

        with pytest.raises(ValidationError, match="The token is invalid or has expired."):
            PasswordService.confirm_password_reset("invalid-token", "NewPass123!")

    @patch('authentication.services.password_service.password_reset_service.get_value')
    def test_confirm_password_reset_user_deleted(self, mock_get_value, active_user):
        """Рідкісний випадок: токен є в Redis, але юзера вже видалили з Бази Даних."""
        fake_token = "valid-token-but-deleted-user"
        mock_get_value.return_value = str(active_user.id)

        active_user.delete()

        with pytest.raises(ValidationError, match="User not found."):
            PasswordService.confirm_password_reset(fake_token, "NewPass123!")
