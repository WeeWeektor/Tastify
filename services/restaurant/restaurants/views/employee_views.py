from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics

from restaurants.models import RestaurantEmployee, Restaurant
from restaurants.permissions import IsRestaurantManagerOrOwner
from restaurants.serializers import RestaurantEmployeeSerializer


@extend_schema_view(
    get=extend_schema(
        tags=['Management (Employees)'],
        summary='Список працівників ресторану',
        description='Отримати список усіх працівників конкретного закладу.'
    ),
    post=extend_schema(
        tags=['Management (Employees)'],
        summary='Додати нового працівника',
        description='Призначає користувачу (за його user_id) певну роль у ресторані.'
    )
)
class EmployeeListCreateView(generics.ListCreateAPIView):
    serializer_class = RestaurantEmployeeSerializer
    permission_classes = [IsRestaurantManagerOrOwner]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['role', 'is_active']

    def get_queryset(self):
        return RestaurantEmployee.objects.filter(restaurant__slug=self.kwargs.get('slug'))

    def perform_create(self, serializer):
        restaurant = get_object_or_404(Restaurant, slug=self.kwargs.get('slug'))
        serializer.save(restaurant=restaurant)


@extend_schema_view(
    get=extend_schema(tags=['Management (Employees)'], summary='Деталі працівника'),
    put=extend_schema(tags=['Management (Employees)'], summary='Оновити дані працівника повністю'),
    patch=extend_schema(
        tags=['Management (Employees)'],
        summary='Оновити дані працівника частково (наприклад, змінити роль)'
    ),
    delete=extend_schema(tags=['Management (Employees)'], summary='Звільнити працівника (Soft Delete)')
)
class EmployeeRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = RestaurantEmployeeSerializer
    permission_classes = [IsRestaurantManagerOrOwner]
    lookup_field = 'pk'

    def get_queryset(self):
        return RestaurantEmployee.objects.filter(restaurant__slug=self.kwargs.get('slug'))

    def perform_destroy(self, instance):
        """
        Не видаляє запис з бази фізично, а робимо Soft Delete.
        """
        instance.is_active = False
        instance.save(update_fields=['is_active'])
