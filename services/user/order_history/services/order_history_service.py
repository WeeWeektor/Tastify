import logging

from order_history.models import OrderHistoryItem
from shared.decorators import invalidate_user_data_cache
from .cache_service import order_history_cache

logger = logging.getLogger(__name__)


class OrderHistoryService:
    @classmethod
    def create_history_item(cls, event_data: dict):
        address = event_data.get('address', {})
        city = address.get('city', '')
        address_line = address.get('address_line', '')
        short_address = f"{city}, {address_line}".strip(", ")

        order_id = event_data.get('order_id')
        user_id = event_data.get('user_id')

        OrderHistoryItem.objects.create(
            order_id=order_id,
            user_id=user_id,
            restaurant_id=event_data.get('restaurant_id'),
            restaurant_name=event_data.get('restaurant_name'),
            total_amount=event_data.get('total_amount'),
            items_summary=event_data.get('items', []),
            status=event_data.get('status', 'CONFIRMED'),
            delivery_address_short=short_address,
            created_at=event_data.get('created_at')
        )

        invalidate_user_data_cache(order_history_cache, str(user_id))
        logger.info(f"Created order history for order {order_id} and invalidated cache for user {user_id}")

    @classmethod
    def update_order_status(cls, event_data: dict):
        order_id = event_data.get('order_id')
        new_status = event_data.get('status')
        user_id = event_data.get('user_id')

        updated = OrderHistoryItem.objects.filter(order_id=order_id).update(status=new_status)

        if updated:
            invalidate_user_data_cache(order_history_cache, str(user_id))
            logger.info(f"Updated order {order_id} to status {new_status} and invalidated cache for user {user_id}")
        else:
            logger.warning(f"OrderHistoryItem with order_id {order_id} not found for update.")
