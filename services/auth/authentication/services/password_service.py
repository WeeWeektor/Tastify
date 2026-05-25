import uuid

from django.contrib.auth import get_user_model
from django.utils import timezone
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

        password_reset_service.store(value=str(user.id), key=reset_token)

        email_template = PasswordResetEmail(to_email=user.email, reset_token=reset_token)
        EmailSenderService.send(email_template)

    @classmethod
    def confirm_password_reset(cls, token: str, new_password: str) -> None:
        """Збереження нового пароля з перевіркою токена."""
        user_id = password_reset_service.get_value(key=token)

        if not user_id:
            raise ValidationError({"token": _("The token is invalid or has expired.")})

        try:
            user = User.objects.get(id=user_id)
            user.set_password(new_password)
            user.last_login = timezone.now()
            user.save(update_fields=['password', 'last_login'])

            password_reset_service.delete(key=token)
        except User.DoesNotExist:
            raise ValidationError({"token": _("User not found.")})
