from django.urls import path

from .views.public_views import RestaurantListView, RestaurantDetailView

app_name = 'restaurants'

urlpatterns = [
    path('', RestaurantListView.as_view(), name='restaurant-list'),
    path('<slug:slug>/', RestaurantDetailView.as_view(), name='restaurant-detail'),
]
