from django.urls import path

from .views import OrderHistoryListView

urlpatterns = [
    path('', OrderHistoryListView.as_view(), name='order-history-list'),
]
