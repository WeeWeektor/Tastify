import re

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers


def validate_no_xss(value):
    """
    Універсальний валідатор для перевірки на відсутність HTML/JS ін'єкцій.
    Може застосовуватися до будь-якого текстового поля в будь-якому мікросервісі.
    """
    if value and re.search(r'[<>]', value):
        raise serializers.ValidationError(
            _("HTML or script injection detected. Please use only plain text.")
        )
    return value
