import urllib.parse

import pyotp
import pytest
from django.contrib.auth import get_user_model

from authentication.services.two_factor_service import TwoFactorService

User = get_user_model()


@pytest.mark.django_db
class TestTwoFactorService:

    @pytest.fixture
    def user(self):
        """Звичайний користувач без увімкненої 2FA."""
        return User.objects.create_user(
            email='totp_user@example.com',
            password='Password123!'
        )

    @pytest.fixture
    def user_with_secret(self, user):
        """Користувач, якому згенерували секрет, але 2FA ще не увімкнено."""
        user.totp_secret = pyotp.random_base32()
        user.save()
        return user

    @pytest.fixture
    def user_with_2fa_enabled(self, user_with_secret):
        """Користувач з повністю налаштованою 2FA."""
        user_with_secret.is_2fa_enabled = True
        user_with_secret.save()
        return user_with_secret

    def test_generate_totp_secret(self, user):
        """Перевірка правильної генерації секрету та посилання для QR-коду."""
        result = TwoFactorService.generate_totp_secret(user)

        assert 'secret' in result
        assert 'uri' in result

        user.refresh_from_db()
        assert user.totp_secret == result['secret']
        assert len(user.totp_secret) == 32

        assert "Tastify" in result['uri']
        encoded_email = urllib.parse.quote(user.email)
        assert encoded_email in result['uri']
        assert result['secret'] in result['uri']

    def test_verify_and_enable_success(self, user_with_secret):
        """Успішне введення правильного коду вмикає 2FA."""
        totp = pyotp.TOTP(user_with_secret.totp_secret)
        valid_code = totp.now()

        result = TwoFactorService.verify_and_enable(user_with_secret, valid_code)

        assert result is True

        user_with_secret.refresh_from_db()
        assert user_with_secret.is_2fa_enabled is True

    def test_verify_and_enable_invalid_code(self, user_with_secret):
        """Введення неправильного коду залишає 2FA вимкненою."""
        invalid_code = "000000"

        result = TwoFactorService.verify_and_enable(user_with_secret, invalid_code)

        assert result is False

        user_with_secret.refresh_from_db()
        assert user_with_secret.is_2fa_enabled is False

    def test_verify_and_enable_no_secret(self, user):
        """Спроба увімкнути 2FA для юзера, який ще не згенерував секрет."""
        result = TwoFactorService.verify_and_enable(user, "123456")

        assert result is False

    def test_verify_login_token_success(self, user_with_2fa_enabled):
        """Успішна перевірка коду під час авторизації."""
        totp = pyotp.TOTP(user_with_2fa_enabled.totp_secret)
        valid_code = totp.now()

        result = TwoFactorService.verify_login_token(user_with_2fa_enabled, valid_code)

        assert result is True

    def test_verify_login_token_invalid_code(self, user_with_2fa_enabled):
        """Неправильний код під час авторизації."""
        result = TwoFactorService.verify_login_token(user_with_2fa_enabled, "999999")

        assert result is False

    def test_verify_login_token_2fa_disabled(self, user_with_secret):
        """
        Перевірка блокується, якщо юзер згенерував секрет,
        але ще не завершив налаштування (is_2fa_enabled=False).
        """
        totp = pyotp.TOTP(user_with_secret.totp_secret)
        valid_code = totp.now()

        result = TwoFactorService.verify_login_token(user_with_secret, valid_code)

        assert result is False

    def test_verify_login_token_no_secret(self, user):
        """Перевірка блокується, якщо юзер взагалі не має налаштувань 2FA."""
        user.is_2fa_enabled = True
        user.save()

        result = TwoFactorService.verify_login_token(user, "123456")

        assert result is False
