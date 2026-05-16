from django.utils.translation import gettext as _
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter, OpenApiTypes
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.serializers import RegisterSerializer
from authentication.services import AuthenticationService


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Реєстрація нового клієнта",
        description="Створює нового користувача з роллю 'customer' та відправляє email для верифікації.",
        request=RegisterSerializer,
        responses={
            201: OpenApiResponse(description='Користувача успішно створено'),
            400: OpenApiResponse(description='Помилка валідації даних'),
        },
        tags=['Authentication']
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        AuthenticationService.register(
            email=serializer.validated_data['email'],
            password=serializer.validated_data['password'],
            role=serializer.validated_data.get('role', 'customer')
        )

        return Response(
            {"message": _("User registered successfully. Please check your email for verification.")},
            status=status.HTTP_201_CREATED
        )


class VerifyEmailView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Підтвердження email",
        description="Активує акаунт користувача за допомогою токена верифікації.",
        parameters=[
            OpenApiParameter(
                name='token',
                description='Токен для підтвердження email',
                required=True,
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY
            )
        ],
        responses={
            200: OpenApiResponse(description='Email успішно підтверджено'),
            400: OpenApiResponse(description='Невірний або прострочений токен'),
        },
        tags=['Authentication']
    )
    def get(self, request):
        token = request.query_params.get('token')

        if not token:
            return Response({"error": _("Token is required.")}, status=status.HTTP_400_BAD_REQUEST)

        AuthenticationService.verify_email(token)
        return Response(
            {"message": _("Your email address has been successfully verified.")},
            status=status.HTTP_200_OK
        )
