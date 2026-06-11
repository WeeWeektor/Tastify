from rest_framework import permissions

from .models import Restaurant, RestaurantEmployee, EmployeeRole


class ReadOnly(permissions.BasePermission):
    """
    Дозволяє доступ всім користувачам, але тільки для безпечних методів (GET, HEAD, OPTIONS).
    """

    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS


class IsPlatformAdmin(permissions.BasePermission):
    """
    Перевіряє, чи є користувач глобальним адміністратором платформи.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return getattr(request.user, 'role', None) == 'admin'


class BaseRestaurantPermission(permissions.BasePermission):
    """
    Базовий клас для перевірки прав працівників ресторану.
    Містить спільну логіку для визначення ID ресторану з різних об'єктів.
    """

    def get_restaurant_id(self, obj):
        if isinstance(obj, Restaurant):
            return obj.id
        if hasattr(obj, 'restaurant_id'):
            return obj.restaurant_id
        if hasattr(obj, 'restaurant'):
            return obj.restaurant.id
        return None

    def check_role(self, request, obj, allowed_roles):
        if not request.user or not request.user.is_authenticated:
            return False

        restaurant_id = self.get_restaurant_id(obj)
        if not restaurant_id:
            return False

        return RestaurantEmployee.objects.filter(
            restaurant_id=restaurant_id,
            user_id=request.user.id,
            role__in=allowed_roles,
            is_active=True
        ).exists()


class IsRestaurantOwner(BaseRestaurantPermission):
    """
    Повний доступ. Тільки для ролі OWNER.
    Використання: Додавання/видалення менеджерів, глобальні налаштування.
    """

    def has_object_permission(self, request, view, obj):
        return self.check_role(request, obj, allowed_roles=[EmployeeRole.OWNER])


class IsRestaurantManagerOrOwner(BaseRestaurantPermission):
    """
    Високий доступ. Для OWNER та MANAGER.
    Використання: Оновлення інформації про ресторан (назва, телефон, графік, is_accepting_orders).
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        return self.check_role(
            request,
            obj,
            allowed_roles=[EmployeeRole.OWNER, EmployeeRole.MANAGER]
        )


class IsMenuEditor(BaseRestaurantPermission):
    """
    Базовий доступ до управління меню. Для всіх активних працівників.
    Використання: Створення, оновлення, видалення категорій та страв меню.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        return self.check_role(
            request,
            obj,
            allowed_roles=[EmployeeRole.OWNER, EmployeeRole.MANAGER, EmployeeRole.EDITOR]
        )
