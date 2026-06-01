from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import FavoriteRestaurantViewSet

router = DefaultRouter()

router.register(r'', FavoriteRestaurantViewSet, basename='favorite')

urlpatterns = [
    path("", include(router.urls)),
]
