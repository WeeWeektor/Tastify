from urllib.parse import urlencode

from django.conf import settings
from django.shortcuts import redirect
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import permissions
from rest_framework.views import APIView

from authentication.services import SocialAuthService


class GoogleOAuthView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Редирект на Google OAuth",
        description="Генерує посилання на Google і перенаправляє туди користувача.",
        responses={302: OpenApiResponse(description='Redirect to Google OAuth')},
        tags=['Social Authentication']
    )
    def get(self, request):
        auth_url = SocialAuthService.get_google_auth_url(request)
        return redirect(auth_url)


class GoogleOAuthCallbackView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Обробка Google OAuth Callback",
        description="Google перенаправляє сюди після успішного логіну. Видає JWT токени та редиректить на фронтенд.",
        responses={200: OpenApiResponse(description='Successful authentication')},
        tags=['Social Authentication']
    )
    def get(self, request):
        tokens = SocialAuthService.process_google_callback(request)

        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')

        params = urlencode({
            'access': tokens['access'],
            'refresh': tokens['refresh']
        })
        redirect_url = f"{frontend_url}/oauth/callback?{params}"

        return redirect(redirect_url)
