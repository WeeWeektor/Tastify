import uuid
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone

from authentication.models import RefreshTokenBlacklist
from authentication.tasks import (
    send_verification_email_task,
    clean_expired_blacklisted_tokens
)


@pytest.mark.django_db
class TestCeleryTasks:

    @patch('authentication.tasks.EmailSenderService.send')
    @patch('authentication.tasks.translation.activate')
    def test_send_verification_email_task_success(self, mock_activate, mock_send):
        """Перевірка успішної відправки листа та перемикання мови."""
        mock_send.return_value = True

        email = "user@example.com"
        token = "secret-token-123"
        language = "uk"

        result = send_verification_email_task(email, token, language)

        assert result is True
        mock_activate.assert_called_once_with(language)
        mock_send.assert_called_once()

        called_args, _ = mock_send.call_args
        email_template = called_args[0]

        assert email_template.to_email == email
        assert email_template.token == token

    @patch('authentication.tasks.EmailSenderService.send')
    def test_send_verification_email_task_failure(self, mock_send):
        """Перевірка поведінки задачі при помилці відправки (наприклад, впав SMTP)."""
        mock_send.return_value = False

        result = send_verification_email_task("test@test.com", "token", "en")

        assert result is False
        mock_send.assert_called_once()

    def test_clean_expired_blacklisted_tokens(self):
        """
        Перевірка, що задача видаляє ТІЛЬКИ протерміновані токени.
        """
        now = timezone.now()
        user_id = uuid.uuid4()

        t1 = RefreshTokenBlacklist.objects.create(
            jti="expired-token-1",
            user_id=user_id,
            expires_at=now + timedelta(days=1)
        )
        t2 = RefreshTokenBlacklist.objects.create(
            jti="expired-token-2",
            user_id=user_id,
            expires_at=now + timedelta(days=1)
        )

        RefreshTokenBlacklist.objects.filter(id=t1.id).update(
            blacklisted_at=now - timedelta(days=2),
            expires_at=now - timedelta(days=1)
        )
        RefreshTokenBlacklist.objects.filter(id=t2.id).update(
            blacklisted_at=now - timedelta(hours=2),
            expires_at=now - timedelta(minutes=5)
        )

        RefreshTokenBlacklist.objects.create(
            jti="valid-token",
            user_id=user_id,
            expires_at=now + timedelta(days=1)
        )

        assert RefreshTokenBlacklist.objects.count() == 3

        deleted_count = clean_expired_blacklisted_tokens()

        assert deleted_count == 2
        assert RefreshTokenBlacklist.objects.count() == 1

        remaining_token = RefreshTokenBlacklist.objects.first()
        assert remaining_token.jti == "valid-token"

    def test_clean_expired_tokens_empty_db(self):
        """Перевірка роботи задачі, якщо база токенів порожня."""
        assert RefreshTokenBlacklist.objects.count() == 0

        deleted_count = clean_expired_blacklisted_tokens()

        assert deleted_count == 0
