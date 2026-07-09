import django_filters

from .models import Restaurant


class RestaurantFilter(django_filters.FilterSet):
    city = django_filters.CharFilter(field_name='city', lookup_expr='iexact')
    cuisine = django_filters.CharFilter(method='filter_by_cuisine')

    class Meta:
        model = Restaurant
        fields = ['city']

    @staticmethod
    def filter_by_cuisine(queryset, name, value):
        """
            Шукає ресторани, у яких масив cuisine_types містить передане значення.
            Наприклад: ?cuisine=pizza знайде запис з cuisine_types=['pizza', 'sushi']
        """
        if value:
            return queryset.filter(cuisine_types__contains=[value.lower()])
        return queryset
