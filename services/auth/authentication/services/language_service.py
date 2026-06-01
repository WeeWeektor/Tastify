import logging

from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError

User = get_user_model()
logger = logging.getLogger(__name__)


class LanguageService:
    @classmethod
    def update_language(cls, user_id: str, language: str) -> None:
        """
            Внутрішній метод для оновлення мови користувача.
        """
        try:
            user = User.objects.get(id=user_id)
            user.language = language
            user.save(update_fields=['language'])
            logger.info(f"Language for user {user_id} updated to {language}")
        except User.DoesNotExist:
            raise ValidationError({"detail": _("User not found.")})
