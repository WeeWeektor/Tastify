from .management_views import RestaurantCreateView, RestaurantUpdateView, RestaurantToggleOrdersView
from .public_views import RestaurantListView, RestaurantDetailView
# from .admin_views import
from .employee_views import EmployeeListCreateView, EmployeeRetrieveUpdateDestroyView
# from .internal_views import

__all__ = [
    'RestaurantListView',
    'RestaurantDetailView',
    'RestaurantCreateView',
    'RestaurantUpdateView',
    'RestaurantToggleOrdersView',
    'EmployeeListCreateView',
    'EmployeeRetrieveUpdateDestroyView',
]
