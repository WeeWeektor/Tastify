from unittest.mock import patch, ANY

import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken

from authentication.models import RefreshTokenBlacklist
from authentication.services.auth_service import AuthenticationService

User = get_user_model()


@pytest.mark.django_db
class TestAuthenticationService:
    @pytest.fixture
    def unverified_user(self):
        """Користувач, який щойно зареєструвався, але ще не підтвердив пошту."""
        return User.objects.create_user(
            email='unverified@test.com',
            password='Password123!',
            is_verified=False
        )

    @pytest.fixture
    def active_user(self):
        """Повністю активний та підтверджений користувач."""
        return User.objects.create_user(
            email='active@test.com',
            password='Password123!',
            is_verified=True,
            role='customer'
        )

    @pytest.fixture
    def user_with_2fa(self):
        """Користувач з увімкненою 2FA."""
        return User.objects.create_user(
            email='2fa_user@test.com',
            password='Password123!',
            is_verified=True,
            is_2fa_enabled=True,
            totp_secret='JBSWY3DPEHPK3PXP'
        )

    @patch('authentication.tasks.send_verification_email_task.delay')
    @patch('authentication.services.auth_service.email_verification_service.store')
    def test_register_success(self, mock_store, mock_task_delay):
        """Успішна реєстрація створює юзера та відправляє лист."""

        user = AuthenticationService.register(
            email='newuser@test.com',
            password='StrongPassword123!',
            role='customer'
        )

        assert user.id is not None
        assert user.email == 'newuser@test.com'
        assert user.is_verified is False

        mock_store.assert_called_once_with(value=str(user.id), key=ANY)

        mock_task_delay.assert_called_once_with(user.email, ANY, ANY)

    @patch('authentication.services.auth_service.email_verification_service.get_value')
    @patch('authentication.services.auth_service.email_verification_service.delete')
    def test_verify_email_success(self, mock_delete, mock_get_value, unverified_user):
        """Успішне підтвердження пошти."""
        fake_token = "valid-uuid-token"
        mock_get_value.return_value = str(unverified_user.id)

        result = AuthenticationService.verify_email(fake_token)

        assert result is True

        unverified_user.refresh_from_db()
        assert unverified_user.is_verified is True
        mock_delete.assert_called_once_with(key=fake_token)

    @patch('authentication.services.auth_service.email_verification_service.get_value')
    def test_verify_email_invalid_token(self, mock_get_value):
        """Помилка, якщо токена немає в Redis."""
        mock_get_value.return_value = None

        with pytest.raises(ValidationError, match="The token is invalid or has expired."):
            AuthenticationService.verify_email("invalid-token")

    def test_login_success_no_2fa(self, active_user):
        """Успішний логін без 2FA повертає токени."""
        result = AuthenticationService.login(
            email='active@test.com',
            password='Password123!',
            ip_address='192.168.1.1'
        )

        assert result['requires_2fa'] is False
        assert result['pre_auth_token'] is None
        assert 'access' in result
        assert 'refresh' in result

        active_user.refresh_from_db()
        assert active_user.last_login_ip == '192.168.1.1'
        assert active_user.last_login is not None

    @patch('authentication.services.auth_service.pre_auth_service.store')
    def test_login_success_with_2fa(self, mock_store, user_with_2fa):
        """Якщо увімкнена 2FA, логін зупиняється на першому кроці і видає pre_auth_token."""
        result = AuthenticationService.login(
            email='2fa_user@test.com',
            password='Password123!'
        )

        assert result['requires_2fa'] is True
        assert result['pre_auth_token'] is not None
        assert result['access'] is None
        assert result['refresh'] is None

        mock_store.assert_called_once_with(value=str(user_with_2fa.id), key=result['pre_auth_token'])

    def test_login_wrong_password(self, active_user):
        with pytest.raises(ValidationError, match="Incorrect email address or password."):
            AuthenticationService.login('active@test.com', 'WrongPass1!')

    def test_login_unverified_user(self, unverified_user):
        with pytest.raises(ValidationError, match="Please confirm your email address before logging in."):
            AuthenticationService.login('unverified@test.com', 'Password123!')

    def test_login_inactive_user(self, active_user):
        active_user.is_active = False
        active_user.save()

        with pytest.raises(ValidationError, match="Your account has been deactivated."):
            AuthenticationService.login('active@test.com', 'Password123!')

    @patch('authentication.services.auth_service.pre_auth_service.get_value')
    @patch('authentication.services.auth_service.pre_auth_service.delete')
    @patch('authentication.services.auth_service.TwoFactorService.verify_login_token')
    def test_verify_2fa_login_success(self, mock_verify_totp, mock_delete, mock_get_value, user_with_2fa):
        """Успішна перевірка коду 2FA видає фінальні токени."""
        fake_pre_auth = "fake-uuid-123"

        mock_get_value.return_value = str(user_with_2fa.id)
        mock_verify_totp.return_value = True

        result = AuthenticationService.verify_2fa_login(
            pre_auth_token=fake_pre_auth,
            code='123456',
            ip_address='10.0.0.5'
        )

        assert result['requires_2fa'] is False
        assert 'access' in result
        assert 'refresh' in result

        mock_delete.assert_called_once_with(key=fake_pre_auth)

        user_with_2fa.refresh_from_db()
        assert user_with_2fa.last_login_ip == '10.0.0.5'

    @patch('authentication.services.auth_service.pre_auth_service.get_value')
    @patch('authentication.services.auth_service.TwoFactorService.verify_login_token')
    def test_verify_2fa_login_invalid_code(self, mock_verify_totp, mock_get_value, user_with_2fa):
        """Неправильний код 2FA генерує помилку."""
        mock_get_value.return_value = str(user_with_2fa.id)
        mock_verify_totp.return_value = False

        with pytest.raises(ValidationError, match="Invalid 2FA code."):
            AuthenticationService.verify_2fa_login("token", "000000")

    @patch('authentication.services.auth_service.token_blacklist_service.get_value')
    @patch('authentication.services.auth_service.token_blacklist_service.store')
    def test_logout_success(self, mock_store, mock_get_value, active_user):
        """Успішний логаут додає токен в Redis та БД."""
        refresh_token = RefreshToken.for_user(active_user)
        refresh_str = str(refresh_token)
        jti = refresh_token.payload.get('jti')

        mock_get_value.return_value = None

        AuthenticationService.logout(refresh_str)

        mock_store.assert_called_once_with(value=str(active_user.id), key=jti)

        assert RefreshTokenBlacklist.objects.filter(jti=jti).exists()

    @patch('authentication.services.auth_service.token_blacklist_service.get_value')
    def test_logout_already_blocked_token(self, mock_get_value, active_user):
        """Якщо токен вже в Redis, має бути помилка."""
        refresh_token = RefreshToken.for_user(active_user)

        mock_get_value.return_value = "already_blocked"

        with pytest.raises(ValidationError, match="The token has already been blocked."):
            AuthenticationService.logout(str(refresh_token))

    def test_logout_invalid_token_format(self):
        """Спроба передати просто якийсь рядок замість JWT токена."""
        with pytest.raises(ValidationError, match="Invalid or expired refresh token."):
            AuthenticationService.logout("not.a.real.jwt.token")
