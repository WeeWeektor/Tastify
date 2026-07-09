from django.urls import path

from .views.management_views import (
    RestaurantCreateView,
    RestaurantUpdateView,
    RestaurantToggleOrdersView
)
from .views.public_views import RestaurantListView, RestaurantDetailView

app_name = 'restaurants'

urlpatterns = [
    path('', RestaurantListView.as_view(), name='restaurant-list'),
    path('<slug:slug>/', RestaurantDetailView.as_view(), name='restaurant-detail'),

    path('manage/create/', RestaurantCreateView.as_view(), name='restaurant-create'),
    path('manage/<slug:slug>/update/', RestaurantUpdateView.as_view(), name='restaurant-update'),
    path('manage/<slug:slug>/toggle-orders/', RestaurantToggleOrdersView.as_view(), name='restaurant-toggle-orders'),
]
