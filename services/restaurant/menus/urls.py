from django.urls import include, path
from .views.public_views import PublicMenuListView, PublicMenuItemDetailView

public_patterns = [
    path('<slug:slug>/', PublicMenuListView.as_view(), name='public-menu-list'),
    path('<slug:slug>/items/<uuid:id>/', PublicMenuItemDetailView.as_view(), name='public-menu-item-detail'),
]

management_patterns = [

]

urlpatterns = [
    path('', include(public_patterns)),
    path('management/', include(management_patterns)),
]
