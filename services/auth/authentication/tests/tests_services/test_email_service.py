from unittest.mock import patch, MagicMock

import pytest

from authentication.services.email_service import (
    EmailSenderService,
    VerificationEmail,
    PasswordResetEmail
)


class TestEmailTemplates:
    """Тестування класів-генераторів контенту для листів."""

    def test_verification_email_generation(self, settings):
        """Перевірка правильної генерації листа підтвердження пошти."""
        settings.FRONTEND_URL = "https://tastify.com"

        template = VerificationEmail(to_email="user@example.com", token="verify-123")
        payload = template.generate()

        assert payload.recipients == ["user@example.com"]
        assert "Registration Confirmation" in payload.subject

        expected_link = "https://tastify.com/verify-email?token=verify-123"
        assert expected_link in payload.message

        assert f'href="{expected_link}"' in payload.html_message

    def test_password_reset_email_generation(self, settings):
        """Перевірка правильної генерації листа скидання пароля."""
        settings.FRONTEND_URL = "https://tastify.com"

        template = PasswordResetEmail(to_email="forgot@example.com", reset_token="reset-456")
        payload = template.generate()

        assert payload.recipients == ["forgot@example.com"]
        assert "Password Reset" in payload.subject

        expected_link = "https://tastify.com/reset-password?token=reset-456"
        assert expected_link in payload.message
        assert f'href="{expected_link}"' in payload.html_message


class TestEmailSenderService:
    """Тестування сервісу відправки (з мокуванням реального SMTP)."""

    @pytest.fixture
    def mock_template(self):
        """Створюємо фейковий шаблон, щоб не залежати від реальних класів."""
        template = MagicMock()
        template.generate.return_value = MagicMock(
            subject="Test Subject",
            message="Test Text Message",
            html_message="<h1>Test HTML</h1>",
            recipients=["test@example.com"]
        )
        return template

    @patch('authentication.services.email_service.send_mail')
    def test_email_sender_success(self, mock_send_mail, settings, mock_template):
        """Сценарій 1: Успішна відправка листа."""
        settings.DEFAULT_FROM_EMAIL = "noreply@tastify.com"

        mock_send_mail.return_value = 1

        result = EmailSenderService.send(mock_template)

        assert result is True

        mock_send_mail.assert_called_once_with(
            subject="Test Subject",
            message="Test Text Message",
            from_email="noreply@tastify.com",
            recipient_list=["test@example.com"],
            html_message="<h1>Test HTML</h1>",
            fail_silently=False
        )

    @patch('authentication.services.email_service.send_mail')
    def test_email_sender_failure(self, mock_send_mail, settings, mock_template):
        """Сценарій 2: Обробка помилки (впав SMTP сервер)."""
        settings.DEFAULT_FROM_EMAIL = "noreply@tastify.com"

        mock_send_mail.side_effect = Exception("SMTP Connection Timeout")

        result = EmailSenderService.send(mock_template)

        assert result is False
        mock_send_mail.assert_called_once()
