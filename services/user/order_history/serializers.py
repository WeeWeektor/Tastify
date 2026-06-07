from drf_spectacular.utils import extend_schema_serializer, OpenApiExample
from rest_framework import serializers

from .models import OrderHistoryItem


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            name="Приклад історії замовлення",
            value={
                "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "order_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
                "restaurant_id": "123e4567-e89b-12d3-a456-426614174000",
                "restaurant_name": "Піца Плюс",
                "restaurant_logo": "https://minio.example.com/logo.png",
                "total_amount": "550.00",
                "items_summary": [
                    {"name": "Піца Маргарита", "qty": 1, "price": 250},
                    {"name": "Сік апельсиновий", "qty": 2, "price": 150}
                ],
                "status": "delivered",
                "rating_given": 5,
                "delivery_address_short": "вул. Хрещатик, 22",
                "created_at": "2026-06-07T14:30:00Z"
            },
            response_only=True,
        )
    ]
)
class OrderHistoryItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderHistoryItem
        fields = [
            'id',
            'order_id',
            'restaurant_id',
            'restaurant_name',
            'restaurant_logo',
            'total_amount',
            'items_summary',
            'status',
            'rating_given',
            'delivery_address_short',
            'created_at'
        ]
        read_only_fields = fields
