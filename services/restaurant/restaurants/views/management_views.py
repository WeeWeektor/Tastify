from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import Restaurant
from ..permissions import IsRestaurantManagerOrOwner
from ..serializers import RestaurantSerializer
from ..services.management_service import create_restaurant_and_assign_owner, toggle_restaurant_orders_status


@extend_schema_view(
    post=extend_schema(
        tags=['Management (Restaurant Dashboard)'],
        summary='Створити новий ресторан',
        description='Створює заклад і автоматично призначає поточного користувача його ВЛАСНИКОМ (роль OWNER).'
    )
)
class RestaurantCreateView(generics.CreateAPIView):
    serializer_class = RestaurantSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        user_id = self.request.user.id
        create_restaurant_and_assign_owner(serializer, user_id)


@extend_schema_view(
    put=extend_schema(
        tags=['Management (Restaurant Dashboard)'],
        summary='Оновити дані ресторану',
        description='Доступно тільки для ролей OWNER та MANAGER цього конкретного закладу.'
    ),
    patch=extend_schema(tags=['Management (Restaurant Dashboard)'])
)
class RestaurantUpdateView(generics.UpdateAPIView):
    queryset = Restaurant.objects.all()
    serializer_class = RestaurantSerializer
    permission_classes = [IsRestaurantManagerOrOwner]
    lookup_field = 'slug'


class RestaurantToggleOrdersView(APIView):
    """
        Швидкий перемикач статусу прийому замовлень (Panic Button).
    """
    permission_classes = [IsRestaurantManagerOrOwner]

    @extend_schema(
        tags=['Management (Restaurant Dashboard)'],
        summary='Перемикач прийому замовлень (Panic Button)',
        description='Миттєво зупиняє або відновлює прийом замовлень для закладу.'
    )
    def post(self, request, slug):
        restaurant = get_object_or_404(Restaurant, slug=slug)
        self.check_object_permissions(request, restaurant)

        new_status = toggle_restaurant_orders_status(restaurant)

        return Response({
            "status": "success",
            "is_accepting_orders": new_status
        }, status=status.HTTP_200_OK)
