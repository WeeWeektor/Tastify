import logging
import uuid
from datetime import datetime, timezone

from django.contrib.auth import get_user_model
from django.contrib.auth.models import update_last_login
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken

from authentication.models import RefreshTokenBlacklist
from authentication.tasks import send_verification_email_task
from .token_service import email_verification_service, token_blacklist_service, pre_auth_service
from .two_factor_service import TwoFactorService

User = get_user_model()
logger = logging.getLogger(__name__)


class AuthenticationService:
    @classmethod
    @transaction.atomic
    def register(cls, email: str, password: str, role: str, **extra_fields) -> User:
        """
             Реєстрація нового користувача.
             Використовує транзакцію, щоб у разі помилки відправки листа юзер не створювався в БД.
        """
        user = User.objects.create_user(email=email, password=password, role=role, **extra_fields)

        verification_token = str(uuid.uuid4())

        email_verification_service.store(user_id=str(user.id), token=verification_token)

        send_verification_email_task.delay(user.email, verification_token)

        return user

    @classmethod
    def verify_email(cls, token: str) -> bool:
        """
            Перевірка токена з Redis та активація акаунту.
        """
        user_id = email_verification_service.get_user_id_from_verification_token(token)

        if not user_id:
            raise ValidationError({"token": _("The token is invalid or has expired.")})

        try:
            user = User.objects.get(id=user_id)
            if not user.is_verified:
                user.is_verified = True
                user.save(update_fields=['is_verified'])

                email_verification_service.delete(token)
            return True
        except User.DoesNotExist:
            raise ValidationError({"token": _("The token is invalid or has expired.")})

    @classmethod
    def _finalize_login(cls, user, ip_address: str = None) -> dict:
        """
            Приватний метод. Викликається тільки після того, як користувач
            ПОВНІСТЮ підтвердив свою особу (пароль + 2FA, якщо увімкнена).
        """
        if ip_address:
            user.last_login_ip = ip_address
            user.save(update_fields=['last_login_ip'])

        update_last_login(None, user)

        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        refresh['role'] = user.role
        refresh['email'] = user.email

        access['role'] = user.role
        access['email'] = user.email

        return {
            "requires_2fa": False,
            "pre_auth_token": None,
            'refresh': str(refresh),
            'access': str(access),
        }

    @classmethod
    def login(cls, email: str, password: str, ip_address: str = None) -> dict:
        """
            Логін користувача з перевіркою двофакторної автентифікації.
        """
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise ValidationError({"detail": _("Incorrect email address or password.")})

        if not user.check_password(password):
            raise ValidationError({"detail": _("Incorrect email address or password.")})

        if not user.is_verified:
            raise ValidationError({"detail": _("Please confirm your email address before logging in.")})

        if not user.is_active:
            raise ValidationError({"detail": _("Your account has been deactivated.")})

        if user.is_2fa_enabled:
            pre_auth_token = str(uuid.uuid4())
            pre_auth_service.store(user_id=str(user.id), token=pre_auth_token)

            return {
                "requires_2fa": True,
                "pre_auth_token": pre_auth_token,
                "refresh": None,
                "access": None,
            }

        return cls._finalize_login(user, ip_address)

    @classmethod
    def verify_2fa_login(cls, pre_auth_token: str, code: str, ip_address: str = None) -> dict:
        """
            Перевіряє 2FA код за тимчасовим токеном і завершує процес авторизації.
        """
        user_id = pre_auth_service.get_user_id_from_verification_token(pre_auth_token)
        if not user_id:
            raise ValidationError({"pre_auth_token": _("The token is invalid or has expired.")})

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise ValidationError({"detail": _("User not found.")})

        if not TwoFactorService.verify_login_token(user, code):
            raise ValidationError({"code": _("Invalid 2FA code.")})

        pre_auth_service.delete(pre_auth_token)

        return cls._finalize_login(user, ip_address)


    @classmethod
    def logout(cls, refresh_token_str: str) -> None:
        """
        Логаут: Додаємо refresh token до чорного списку (RefreshTokenBlacklist).
        """
        try:
            token = RefreshToken(refresh_token_str)
            jti = token.payload.get('jti')
            user_id = token.payload.get('user_id')
            exp_timestamp = token.payload.get('exp')

            expires_at = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)

            if token_blacklist_service.get_user_id_from_verification_token(jti):
                raise ValidationError({"detail": _("The token has already been blocked.")})

            token_blacklist_service.store(user_id=str(user_id), token=jti)

            if not RefreshTokenBlacklist.objects.filter(jti=jti).exists():
                RefreshTokenBlacklist.objects.create(
                    jti=jti,
                    user_id=user_id,
                    expires_at=expires_at
                )
        except Exception as e:
            logger.error(f"Logout failed for token {refresh_token_str[-10:]}: {str(e)}")
            raise ValidationError({"detail": _("Invalid or expired refresh token.")})
