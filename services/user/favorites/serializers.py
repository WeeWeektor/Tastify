from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample

from .models import FavoriteRestaurant


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            name="Приклад додавання в улюблені",
            value={
                "restaurant_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "restaurant_snapshot": {
                    "name": "Піца Плюс",
                    "logo_url": "https://minio.example.com/logo.png",
                    "rating": 4.8,
                    "...": "інші поля"
                }
            },
            request_only=True,
        )
    ]
)
class FavoriteRestaurantSerializer(serializers.ModelSerializer):
    class Meta:
        model = FavoriteRestaurant
        fields = [
            'id',
            'user_id',
            'restaurant_id',
            'restaurant_snapshot',
            'added_at'
        ]
        read_only_fields = ['id', 'user_id', 'added_at']

    def validate(self, attrs):
        request = self.context.get('request')
        user_id = getattr(request.user, 'id', None) if request and hasattr(request, 'user') else None

        restaurant_id = attrs.get('restaurant_id')

        if user_id and restaurant_id:
            if FavoriteRestaurant.objects.filter(user_id=user_id, restaurant_id=restaurant_id).exists():
                raise serializers.ValidationError(
                    {"restaurant_id": _("This restaurant is already in your favorites.")}
                )

        return attrs
