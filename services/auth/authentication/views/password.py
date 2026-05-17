from django.utils.translation import gettext as _
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from authentication.services import PasswordService

from authentication.serializers import PasswordResetRequestSerializer, PasswordResetConfirmSerializer


class PasswordResetRequestView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Запит на скидання пароля",
        description="Відправляє email з посиланням для скидання пароля, якщо користувач існує.",
        request=PasswordResetRequestSerializer,
        responses={200: OpenApiResponse(description='Якщо email існує, лист буде відправлено')},
        tags=['Password Management']
    )
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        PasswordService.request_password_reset(serializer.validated_data['email'])

        return Response(
            {"message": _("If an account with this email exists, a password reset link has been sent.")},
            status=status.HTTP_200_OK
        )


class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Підтвердження нового пароля",
        description="Встановлює новий пароль для користувача за допомогою токена з email.",
        request=PasswordResetConfirmSerializer,
        responses={
            200: OpenApiResponse(description='Пароль успішно змінено'),
            400: OpenApiResponse(description='Невірний токен або паролі не співпадають'),
        },
        tags=['Password Management']
    )
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        PasswordService.confirm_password_reset(
            token=serializer.validated_data['token'],
            new_password=serializer.validated_data['password']
        )

        return Response(
            {"message": _("Your password has been successfully reset.")},
            status=status.HTTP_200_OK
        )
