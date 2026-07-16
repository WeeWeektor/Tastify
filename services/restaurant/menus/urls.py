from django.urls import include, path

from .views.management_views import (
    ManagementProductListCreateView,
    ManagementProductDetailView,
    ManagementCategoryListCreateView,
    ManagementCategoryDetailView,
    ManagementMenuItemListCreateView,
    ManagementMenuItemDetailView,
    ManagementModifierGroupListCreateView,
    ManagementModifierGroupDetailView,
    ManagementModifierOptionListCreateView,
    ManagementModifierOptionDetailView
)
from .views.public_views import PublicMenuListView, PublicMenuItemDetailView

public_patterns = [
    path('<slug:restaurant_slug>/', PublicMenuListView.as_view(), name='public-menu-list'),
    path('<slug:restaurant_slug>/items/<uuid:id>/', PublicMenuItemDetailView.as_view(), name='public-menu-item-detail'),
]

management_patterns = [
    path('<slug:restaurant_slug>/products/', ManagementProductListCreateView.as_view(), name='management-product-list'),
    path('<slug:restaurant_slug>/products/<uuid:pk>/', ManagementProductDetailView.as_view(),
         name='management-product-detail'),

    path('<slug:restaurant_slug>/categories/', ManagementCategoryListCreateView.as_view(),
         name='management-category-list'),
    path('<slug:restaurant_slug>/categories/<uuid:pk>/', ManagementCategoryDetailView.as_view(),
         name='management-category-detail'),

    path('<slug:restaurant_slug>/items/', ManagementMenuItemListCreateView.as_view(), name='management-item-list'),
    path('<slug:restaurant_slug>/items/<uuid:pk>/', ManagementMenuItemDetailView.as_view(),
         name='management-item-detail'),

    path('<slug:restaurant_slug>/items/<uuid:item_id>/modifier-groups/',
         ManagementModifierGroupListCreateView.as_view(), name='management-modifier-group-list'),
    path('<slug:restaurant_slug>/modifier-groups/<uuid:pk>/', ManagementModifierGroupDetailView.as_view(),
         name='management-modifier-group-detail'),

    path('<slug:restaurant_slug>/modifier-groups/<uuid:group_id>/options/',
         ManagementModifierOptionListCreateView.as_view(), name='management-modifier-option-list'),
    path('<slug:restaurant_slug>/modifier-options/<uuid:pk>/', ManagementModifierOptionDetailView.as_view(),
         name='management-modifier-option-detail'),
]

urlpatterns = [
    path('', include(public_patterns)),
    path('management/', include(management_patterns)),
]
