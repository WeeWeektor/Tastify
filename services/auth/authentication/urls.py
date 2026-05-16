from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from authentication.views import RegisterView, VerifyEmailView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('verify-email/', VerifyEmailView.as_view(), name='verify-email'),

    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
