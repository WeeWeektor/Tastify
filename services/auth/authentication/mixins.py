from django.utils.translation import gettext_lazy as _
from rest_framework import serializers


class PasswordValidationAndConfirmationMixin:
    """
    Міксин для валідації пароля та його підтвердження.
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        min_length=8,
        style={'input_type': 'password'},
        help_text=_('The password must be at least 8 characters long.'),
        error_messages={
            'required': _('Password is required.'),
            'blank': _('Password cannot be blank.'),
            'min_length': _('Ensure this field has at least 8 characters.')
        }
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        error_messages={
            'required': _('Password confirmation is required.'),
            'blank': _('Password confirmation cannot be blank.')
        }
    )

    def validate(self, attrs):
        if attrs.get('password') != attrs.get('password_confirm'):
            raise serializers.ValidationError({
                "password_confirm": _("Passwords do not match.")
            })
        return attrs
