from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import AuthenticationFailed
from social_core.exceptions import AuthException

from authentication.services.social_service import SocialAuthService

User = get_user_model()


@pytest.mark.django_db
class TestSocialAuthService:

    @pytest.fixture
    def active_user(self):
        """Звичайний активний користувач."""
        return User.objects.create_user(
            email='google_user@example.com',
            password='RandomPassword123!',
            is_active=True
        )

    @pytest.fixture
    def inactive_user(self):
        """Деактивований користувач."""
        return User.objects.create_user(
            email='banned_user@example.com',
            password='RandomPassword123!',
            is_active=False
        )

    @pytest.fixture
    def mock_request(self):
        """Фейковий об'єкт запиту для передачі в методи."""
        return MagicMock()

    @patch('authentication.services.social_service.load_backend')
    @patch('authentication.services.social_service.load_strategy')
    def test_get_backend(self, mock_load_strategy, mock_load_backend, settings, mock_request):
        """Перевірка правильної ініціалізації OAuth бекенду з налаштувань."""
        expected_callback_url = "https://tastify.com/api/v1/auth/google/callback/"
        settings.GOOGLE_OAUTH2_CALLBACK_URL = expected_callback_url

        mock_strategy = MagicMock()
        mock_load_strategy.return_value = mock_strategy

        mock_backend_instance = MagicMock()
        mock_load_backend.return_value = mock_backend_instance

        backend = SocialAuthService._get_backend(mock_request)

        assert backend == mock_backend_instance

        mock_load_strategy.assert_called_once_with(mock_request)

        mock_load_backend.assert_called_once_with(
            strategy=mock_strategy,
            name='google-oauth2',
            redirect_uri=expected_callback_url
        )

    @patch.object(SocialAuthService, '_get_backend')
    def test_get_google_auth_url(self, mock_get_backend, mock_request):
        """Перевіряємо, чи сервіс правильно викликає метод auth_url() у бекенду."""
        expected_url = "https://accounts.google.com/o/oauth2/v2/auth?client_id=..."

        mock_backend = MagicMock()
        mock_backend.auth_url.return_value = expected_url
        mock_get_backend.return_value = mock_backend

        url = SocialAuthService.get_google_auth_url(mock_request)

        assert url == expected_url
        mock_get_backend.assert_called_once_with(mock_request)
        mock_backend.auth_url.assert_called_once()

    @patch.object(SocialAuthService, '_get_backend')
    def test_process_google_callback_success(self, mock_get_backend, mock_request, active_user):
        """Успішна авторизація: користувач існує і активний, видаються JWT токени."""
        mock_backend = MagicMock()
        mock_backend.complete.return_value = active_user
        mock_get_backend.return_value = mock_backend

        result = SocialAuthService.process_google_callback(mock_request)

        assert 'access' in result
        assert 'refresh' in result

        mock_backend.complete.assert_called_once_with(user=None)

    @patch.object(SocialAuthService, '_get_backend')
    def test_process_google_callback_inactive_user(self, mock_get_backend, mock_request, inactive_user):
        """Користувач успішно пройшов Google, але його акаунт у нас деактивований."""
        mock_backend = MagicMock()
        mock_backend.complete.return_value = inactive_user
        mock_get_backend.return_value = mock_backend

        with pytest.raises(AuthenticationFailed, match="User is disabled or not found."):
            SocialAuthService.process_google_callback(mock_request)

    @patch.object(SocialAuthService, '_get_backend')
    def test_process_google_callback_user_not_returned(self, mock_get_backend, mock_request):
        """Бекенд відпрацював без помилок, але повернув None замість юзера."""
        mock_backend = MagicMock()
        mock_backend.complete.return_value = None
        mock_get_backend.return_value = mock_backend

        with pytest.raises(AuthenticationFailed, match="User is disabled or not found."):
            SocialAuthService.process_google_callback(mock_request)

    @patch.object(SocialAuthService, '_get_backend')
    def test_process_google_callback_auth_exception(self, mock_get_backend, mock_request):
        """Google відхилив авторизацію (недійсний код). Специфічна помилка AuthException."""
        mock_backend = MagicMock()
        error_msg = "Token missing"
        mock_backend.complete.side_effect = AuthException(mock_backend, error_msg)
        mock_get_backend.return_value = mock_backend

        with pytest.raises(AuthenticationFailed) as exc_info:
            SocialAuthService.process_google_callback(mock_request)

        assert "Google authentication failed" in str(exc_info.value)
        assert error_msg in str(exc_info.value)

    @patch.object(SocialAuthService, '_get_backend')
    def test_process_google_callback_general_exception(self, mock_get_backend, mock_request):
        """Непередбачувана помилка (впала база даних або мережа під час виконання callback)."""
        mock_backend = MagicMock()
        mock_backend.complete.side_effect = Exception("Database connection lost")
        mock_get_backend.return_value = mock_backend

        with pytest.raises(AuthenticationFailed, match="An error occurred during authentication."):
            SocialAuthService.process_google_callback(mock_request)
