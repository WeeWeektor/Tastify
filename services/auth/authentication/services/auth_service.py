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
from .token_service import email_verification_service, token_blacklist_service

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
    def login(cls, email: str, password: str, ip_address: str = None) -> dict:
        """
            Логін користувача з генерацією JWT токенів та логуванням IP.
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

        if ip_address:
            user.last_login_ip = ip_address
            user.save(update_fields=['last_login_ip'])

        update_last_login(None, user)

        refresh = RefreshToken.for_user(user)

        refresh['role'] = user.role
        refresh['email'] = user.email

        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

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
