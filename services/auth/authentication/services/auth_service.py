import logging
import uuid

from django.contrib.auth import get_user_model
from django.db import transaction

from .email_service import VerificationEmail, EmailSenderService
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

        email_template = VerificationEmail(to_email=user.email, token=verification_token)
        email_sent = EmailSenderService.send(email_template)

        if not email_sent:
            logger.warning(f"Registration email to {email} was not sent, but user was created.")

        return user
