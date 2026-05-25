from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import permissions, status, views
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from shared import get_client_ip

from authentication.serializers import Code2FASerializer, Verify2FALoginSerializer
from authentication.services import AuthenticationService, TwoFactorService

User = get_user_model()


class Setup2FAView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Налаштування двофакторної аутентифікації",
        description="Генерує секретний ключ та QR-код для налаштування 2FA у додатку-генераторі кодів.",
        request=None,
        responses={
            200: OpenApiResponse(description='Успішно згенеровано секретний ключ та QR-код'),
            401: OpenApiResponse(description='Неавторизований доступ'),
        },
        tags=['Two-Factor Authentication']
    )
    def post(self, request):
        data = TwoFactorService.generate_totp_secret(request.user)
        return Response(data, status=status.HTTP_200_OK)


class Enable2FAView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Підтвердження та увімкнення 2FA",
        description="Перевіряє код з додатку-генератора та вмикає 2FA для акаунта.",
        request=Code2FASerializer,
        responses={
            200: OpenApiResponse(description='2FA успішно увімкнено'),
            400: OpenApiResponse(description='Невірний код або 2FA не налаштовано'),
            401: OpenApiResponse(description='Неавторизований доступ'),
        },
        tags=['Two-Factor Authentication']
    )
    def post(self, request):
        serializer = Code2FASerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        success = TwoFactorService.verify_and_enable(
            user=request.user,
            code=serializer.validated_data['code']
        )

        if not success:
            raise ValidationError({"code": _("Invalid 2FA code. Verification failed.")})

        return Response(
            {"detail": _("Two-factor authentication enabled successfully.")},
            status=status.HTTP_200_OK
        )


class Verify2FALoginView(views.APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Підтвердження 2FA під час логіну",
        description="Перевіряє код 2FA після успішної перевірки пароля та повертає JWT токени.",
        request=Verify2FALoginSerializer,
        responses={
            200: OpenApiResponse(description='Успішна авторизація з 2FA'),
            400: OpenApiResponse(description='Невірний код або відсутній pre-auth токен'),
            401: OpenApiResponse(description='Невірні облікові дані або не підтверджений email'),
        },
        tags=['Two-Factor Authentication']
    )
    def post(self, request):
        serializer = Verify2FALoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ip_address = get_client_ip(request)
        tokens = AuthenticationService.verify_2fa_login(
            pre_auth_token=serializer.validated_data['pre_auth_token'],
            code=serializer.validated_data['code'],
            ip_address=ip_address
        )

        return Response({
            "refresh": tokens["refresh"],
            "access": tokens["access"]
        }, status=status.HTTP_200_OK)
