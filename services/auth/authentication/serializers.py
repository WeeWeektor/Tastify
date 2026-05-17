from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from authentication.mixins import PasswordValidationAndConfirmationMixin
from authentication.models import RefreshTokenBlacklist
from authentication.services.token_service import token_blacklist_service

User = get_user_model()


class RegisterSerializer(PasswordValidationAndConfirmationMixin, serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'password', 'password_confirm', 'role')
        extra_kwargs = {
            'email': {'required': True},
            'role': {'required': True},
        }
        read_only_fields = ('id',)

    def create(self, validated_data):
        validated_data.pop('password_confirm', None)
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            role=validated_data.get('role', 'customer')
        )
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(
        required=True,
        error_messages={
            'required': _('Email is required.'),
            'invalid': _('Enter a valid email address.'),
            'blank': _('Email cannot be blank.')
        }
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
        error_messages={
            'required': _('Email is required.'),
            'invalid': _('Enter a valid email address.'),
            'blank': _('Email cannot be blank.')
        }
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

        if token_blacklist_service.get_user_id_from_verification_token(jti):
            raise InvalidToken(_("This token has been blacklisted."))

        if RefreshTokenBlacklist.objects.filter(jti=jti).exists():
            raise InvalidToken(_("This token has been blacklisted."))

        return data
