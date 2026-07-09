from django.db import transaction

from ..models import RestaurantEmployee, EmployeeRole, Restaurant


@transaction.atomic
def create_restaurant_and_assign_owner(serializer, user_id: str):
    """
        Бізнес-логіка створення ресторану.
        Гарантує, що ресторан і його власник створюються одночасно.
        Якщо щось піде не так, відкочуються обидві операції.
    """
    restaurant = serializer.save()

    RestaurantEmployee.objects.create(
        restaurant=restaurant,
        user_id=user_id,
        role=EmployeeRole.OWNER
    )

    return restaurant

def toggle_restaurant_orders_status(restaurant: Restaurant) -> bool:
    """
        Перемикає статус прийому замовлень ресторану та зберігає зміни.
    """
    restaurant.is_accepting_orders = not restaurant.is_accepting_orders
    restaurant.save(update_fields=['is_accepting_orders', 'updated_at'])

    # TODO логіка Kafka
    #      kafka_producer.send_event('restaurant.status_changed', {
    #     'restaurant_id': str(restaurant.id),
    #     'is_accepting_orders': restaurant.is_accepting_orders
    # })

    return restaurant.is_accepting_orders
