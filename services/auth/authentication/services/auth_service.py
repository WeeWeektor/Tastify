import logging
import uuid

from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from authentication.tasks import send_verification_email_task
from .token_service import email_verification_service

User = get_user_model()
logger = logging.getLogger(__name__)


class AuthenticationService:
    @staticmethod
    @transaction.atomic
    def register(email: str, password: str, role: str, **extra_fields) -> User:
        """
             Реєстрація нового користувача.
             Використовує транзакцію, щоб у разі помилки відправки листа юзер не створювався в БД.
        """
        user = User.objects.create_user(email=email, password=password, role=role, **extra_fields)

        verification_token = str(uuid.uuid4())

        email_verification_service.store(user_id=str(user.id), token=verification_token)

        send_verification_email_task.delay(user.email, verification_token)

        return user

    @staticmethod
    def verify_email(token: str) -> bool:
        """
            Перевірка токена з Redis та активація акаунту.
        """
        user_id = email_verification_service.get_user_id_from_verification_token(token)

        if not user_id:
            raise ValidationError({"token": _("The token is invalid or has expired.")})

        try:
            user = User.objects.get(id=user_id)
            if user.is_verified:
                return True

            user.is_verified = True
            user.save(update_fields=['is_verified'])

            email_verification_service.delete(token)
            return True
        except User.DoesNotExist:
            raise ValidationError({"token": _("The token is invalid or has expired.")})
