from django.urls import path, include

from authentication.views import (
    RegisterView,
    VerifyEmailView,
    LoginView,
    LogoutView,
    CustomTokenRefreshView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    GoogleOAuthView,
    GoogleOAuthCallbackView,
)

auth_patterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('verify-email/', VerifyEmailView.as_view(), name='verify-email'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
]

password_patterns = [
    path('reset/', PasswordResetRequestView.as_view(), name='password_reset'),
    path('reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
]

social_patterns = [
    path('google/', GoogleOAuthView.as_view(), name='google_login'),
    path('google/callback/', GoogleOAuthCallbackView.as_view(), name='google_callback'),
]

two_factor_patterns = [

]

urlpatterns = [
    path('', include(auth_patterns)),
    path('password/', include(password_patterns)),
    path('social/', include(social_patterns)),
    path('2fa/', include(two_factor_patterns)),
]
