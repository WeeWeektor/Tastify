import uuid

from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError

from .email_service import EmailSenderService, PasswordResetEmail
from .token_service import password_reset_service

User = get_user_model()


class PasswordService:
    @classmethod
    def request_password_reset(cls, email: str) -> None:
        """Відправка листа з токеном для скидання пароля."""
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return

        if not user.is_active or not user.is_verified:
            return

        reset_token = str(uuid.uuid4())

        password_reset_service.store(user_id=str(user.id), token=reset_token)

        email_template = PasswordResetEmail(to_email=user.email, reset_token=reset_token)
        EmailSenderService.send(email_template)

    @classmethod
    def confirm_password_reset(cls, token: str, new_password: str) -> None:
        """Збереження нового пароля з перевіркою токена."""
        user_id = password_reset_service.get_user_id_from_verification_token(token)

        if not user_id:
            raise ValidationError({"token": _("The token is invalid or has expired.")})

        try:
            user = User.objects.get(id=user_id)
            user.set_password(new_password)
            user.save(update_fields=['password'])

            password_reset_service.delete(token)
        except User.DoesNotExist:
            raise ValidationError({"token": _("User not found.")})
