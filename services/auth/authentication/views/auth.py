from django.utils.translation import gettext as _
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter, OpenApiTypes
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenRefreshView

from authentication.serializers import RegisterSerializer, LoginSerializer, LogoutSerializer, \
    CustomTokenRefreshSerializer
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


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Авторизація користувача",
        description="Авторизує користувача та повертає JWT токени.",
        request=LoginSerializer,
        responses={
            200: OpenApiResponse(description='Успішна авторизація'),
            400: OpenApiResponse(description='Помилка валідації даних'),
            401: OpenApiResponse(description='Невірні облікові дані або не підтверджений email'),
        },
        tags=['Authentication']
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')

        tokens = AuthenticationService.login(
            email=serializer.validated_data['email'],
            password=serializer.validated_data['password'],
            ip_address=ip
        )

        return Response(tokens, status=status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Вихід з системи",
        description=(
                "Блокує refresh токен, щоб користувач не міг використовувати його для отримання нових access токенів."
        ),
        request=LogoutSerializer,
        responses={
            204: OpenApiResponse(description='Успішний вихід, токен заблоковано'),
            400: OpenApiResponse(description='Невірний або відсутній токен'),
            401: OpenApiResponse(description='Користувач не авторизований'),
        },
        tags=['Authentication']
    )
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        AuthenticationService.logout(serializer.validated_data['refresh'])

        return Response(status=status.HTTP_204_NO_CONTENT)


class CustomTokenRefreshView(TokenRefreshView):
    """
    Перевизначений ендпоінт для оновлення access токена.
    Він автоматично використовує логіку перевірки чорного списку.
    """
    serializer_class = CustomTokenRefreshSerializer

    @extend_schema(
        summary="Оновлення JWT токена (Refresh)",
        description="Приймає якісний refresh токен, перевіряє його за чорними списками Redis/БД і видає новий свіжий access токен.",
        tags=['Authentication']
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
