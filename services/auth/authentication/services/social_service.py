from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken
from social_core.exceptions import AuthException
from social_django.utils import load_strategy, load_backend

User = get_user_model()


class SocialAuthService:
    @classmethod
    def _get_backend(cls, request):
        strategy = load_strategy(request)
        backend = load_backend(
            strategy=strategy,
            name='google-oauth2',
            redirect_uri=settings.GOOGLE_OAUTH2_CALLBACK_URL
        )
        return backend

    @classmethod
    def get_google_auth_url(cls, request) -> str:
        """
            Генерує URL для редиректу на сторінку авторизації Google.
        """
        backend = cls._get_backend(request)
        return backend.auth_url()

    @classmethod
    def process_google_callback(cls, request) -> dict:
        """
            Обробляє відповідь від Google, створює/знаходить юзера і видає JWT.
        """
        backend = cls._get_backend(request)

        try:
            user = backend.complete(user=None)
        except AuthException as e:
            raise AuthenticationFailed(f"{_('Google authentication failed:')} {str(e)}")
        except Exception as e:
            raise AuthenticationFailed(_("An error occurred during authentication."))

        if not user or not user.is_active:
            raise AuthenticationFailed(_("User is disabled or not found."))

        refresh = RefreshToken.for_user(user)

        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
