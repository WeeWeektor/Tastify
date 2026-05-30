import logging

import jwt
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

logger = logging.getLogger(__name__)


class MicroserviceUser:
    """
    Фейковий об'єкт користувача.
    Потрібен DRF для того, щоб request.user.id працював коректно,
    без необхідності створювати таблицю auth_user у кожному мікросервісі.
    """

    def __init__(self, user_id, role='customer'):
        self.id = user_id
        self.pk = user_id
        self.role = role
        self.is_authenticated = True
        self.is_active = True

    def __str__(self):
        return str(self.id)


class MicroserviceJWTAuthentication(BaseAuthentication):
    """
    Кастомний клас авторизації для мікросервісів.
    Він тільки валідує JWT токен (перевіряє підпис) і повертає MicroserviceUser.
    """

    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')

        if not auth_header or not auth_header.startswith('Bearer '):
            return None

        token = auth_header.split(' ')[1]

        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=['HS256']
            )

            user_id = payload.get('user_id')
            role = payload.get('role')

            if not user_id:
                raise AuthenticationFailed(_('Token contained no recognizable user identification'))

            return MicroserviceUser(user_id=user_id, role=role), token

        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed(_('Token has expired'))
        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid JWT Token: {e}")
            raise AuthenticationFailed(_('Invalid token'))


class MicroserviceJWTAuthenticationScheme(OpenApiAuthenticationExtension):
    target_class = 'shared.auth_backend.MicroserviceJWTAuthentication'
    name = 'jwtAuth'

    def get_security_definition(self, auto_schema):
        return {
            'type': 'http',
            'scheme': 'bearer',
            'bearerFormat': 'JWT',
        }
