from datetime import datetime, timezone

from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from authentication.mixins import PasswordValidationAndConfirmationMixin
from authentication.models import RefreshTokenBlacklist
from authentication.services.token_service import token_blacklist_service

User = get_user_model()

EMAIL_FIELD_ERROR_MESSAGES = {
    'required': _('Email is required.'),
    'invalid': _('Enter a valid email address.'),
    'blank': _('Email cannot be blank.')
}

CODE_FIELD_ERROR_MESSAGES = {
    'required': _('Code is required.'),
    'min_length': _('Code must be exactly 6 digits.'),
    'max_length': _('Code must be exactly 6 digits.')
}


class RegisterSerializer(PasswordValidationAndConfirmationMixin):
    email = serializers.EmailField(
        required=True,
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message=_('A user with that email already exists.')
            )
        ],
        error_messages=EMAIL_FIELD_ERROR_MESSAGES
    )

    class Meta:
        model = User
        fields = ('id', 'email', 'password', 'password_confirm')
        extra_kwargs = {
            'email': {'required': True},
        }
        read_only_fields = ('id',)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(
        required=True,
        error_messages=EMAIL_FIELD_ERROR_MESSAGES
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        error_messages={
            'required': _('Password is required.'),
            'blank': _('Password cannot be blank.')
        }
    )


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(
        required=True,
        help_text=_("Refresh token, which needs to be blocked."),
        error_messages={
            'required': _('Refresh token is required.'),
            'blank': _('Refresh token cannot be blank.')
        }
    )


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(
        required=True,
        help_text=_("The email address of the user who has forgotten their password."),
        error_messages=EMAIL_FIELD_ERROR_MESSAGES
    )


class PasswordResetConfirmSerializer(PasswordValidationAndConfirmationMixin, serializers.Serializer):
    token = serializers.CharField(
        required=True,
        error_messages={
            'required': _('Token is required.'),
            'blank': _('Token cannot be blank.')
        }
    )


class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    """
    Кастомний серіалізатор оновлення токенів з подвійною перевіркою чорного списку.
    """

    def validate(self, attrs):
        data = super().validate(attrs)

        refresh_token_str = attrs['refresh']
        refresh = RefreshToken(refresh_token_str)
        jti = refresh.payload.get('jti')

        user_id = refresh.payload.get('user_id')
        iat_timestamp = refresh.payload.get('iat')

        if token_blacklist_service.get_value(key=jti):
            raise InvalidToken(_("This token has been blacklisted."))

        if RefreshTokenBlacklist.objects.filter(jti=jti).exists():
            raise InvalidToken(_("This token has been blacklisted."))

        try:
            user = User.objects.get(id=user_id)
            token_issued_at = datetime.fromtimestamp(iat_timestamp, tz=timezone.utc)

            if user.last_login and token_issued_at < user.last_login:
                raise InvalidToken(_("Password was changed. Please log in again."))
        except User.DoesNotExist:
            raise InvalidToken(_("User not found."))

        return data


class Code2FASerializer(serializers.Serializer):
    code = serializers.CharField(
        max_length=6,
        min_length=6,
        required=True,
        error_messages=CODE_FIELD_ERROR_MESSAGES
    )


class Verify2FALoginSerializer(serializers.Serializer):
    pre_auth_token = serializers.CharField(
        required=True,
        error_messages={
            'required': _('Pre-auth token is required.')
        }
    )
    code = serializers.CharField(
        max_length=6,
        min_length=6,
        required=True,
        error_messages=CODE_FIELD_ERROR_MESSAGES
    )
