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
    Вміє перевіряти права як для конкретного об'єкта, так і для URL-шляху (slug).
    """

    def _get_user_id(self, request):
        """Витягує user_id з урахуванням кастомного JWT контексту."""
        if hasattr(request, 'user') and getattr(request.user, 'id', None):
            return str(request.user.id)
        if hasattr(request, 'user_context') and isinstance(request.user_context, dict):
            return str(request.user_context.get('user_id'))
        return None

    def _get_restaurant_id_from_obj(self, obj):
        """Достає ID ресторану з будь-якого об'єкта моделі."""
        if isinstance(obj, Restaurant):
            return obj.id
        if hasattr(obj, 'restaurant_id'):
            return obj.restaurant_id
        if hasattr(obj, 'restaurant'):
            return obj.restaurant.id
        return None

    def _check_role(self, request, allowed_roles, restaurant_id=None, restaurant_slug=None):
        """Головна логіка перевірки в базі даних."""
        user_id = self._get_user_id(request)
        if not user_id:
            return False

        query = RestaurantEmployee.objects.filter(
            user_id=user_id,
            role__in=allowed_roles,
            is_active=True
        )

        if restaurant_id:
            return query.filter(restaurant_id=restaurant_id).exists()
        elif restaurant_slug:
            return query.filter(restaurant__slug=restaurant_slug).exists()

        return False


class IsRestaurantOwner(BaseRestaurantPermission):
    """Тільки для ролі OWNER (наприклад, додавання/видалення менеджерів)."""

    def has_permission(self, request, view):
        slug = view.kwargs.get('slug')
        if slug:
            return self._check_role(request, [EmployeeRole.OWNER], restaurant_slug=slug)
        return True

    def has_object_permission(self, request, view, obj):
        rest_id = self._get_restaurant_id_from_obj(obj)
        return self._check_role(request, [EmployeeRole.OWNER], restaurant_id=rest_id)


class IsRestaurantManagerOrOwner(BaseRestaurantPermission):
    """Для OWNER та MANAGER (наприклад, оновлення налаштувань, найм працівників)."""

    def has_permission(self, request, view):
        slug = view.kwargs.get('slug')
        if slug:
            return self._check_role(request, [EmployeeRole.OWNER, EmployeeRole.MANAGER], restaurant_slug=slug)
        return True

    def has_object_permission(self, request, view, obj):
        rest_id = self._get_restaurant_id_from_obj(obj)
        return self._check_role(request, [EmployeeRole.OWNER, EmployeeRole.MANAGER], restaurant_id=rest_id)


class IsMenuEditor(BaseRestaurantPermission):
    """Для всіх активних працівників (OWNER, MANAGER, EDITOR)."""

    def has_permission(self, request, view):
        slug = view.kwargs.get('restaurant_slug')
        if slug:
            return self._check_role(
                request,
                [EmployeeRole.OWNER, EmployeeRole.MANAGER, EmployeeRole.EDITOR],
                restaurant_slug=slug
            )
        return True

    def has_object_permission(self, request, view, obj):
        rest_id = self._get_restaurant_id_from_obj(obj)
        return self._check_role(
            request,
            [EmployeeRole.OWNER, EmployeeRole.MANAGER, EmployeeRole.EDITOR],
            restaurant_id=rest_id
        )
