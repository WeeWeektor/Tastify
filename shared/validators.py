import re

from django.core.files.uploadedfile import UploadedFile
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


def validate_image(file: UploadedFile):
    max_size = 5 * 1024 * 1024
    if file.size > max_size:
        raise serializers.ValidationError({"file": _("Image size should not exceed 5MB.")})

    allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
    if file.content_type not in allowed_types:
        raise serializers.ValidationError({
            "file": _("Unsupported image type format. Allowed types: JPEG, PNG, GIF, WEBP.")
        })


def validate_phone(value):
    if value:
        cleaned_value = re.sub(r'[\s\-()]+', '', value)

        if not re.match(r'^\+?\d{10,15}$', cleaned_value):
            raise serializers.ValidationError(_("Invalid phone number format."))
        return cleaned_value
    return value
