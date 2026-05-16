from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from authentication.views import RegisterView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),

    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
