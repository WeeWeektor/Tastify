import logging

from .services import OrderHistoryService

logger = logging.getLogger(__name__)


def handle_order_events(payload: dict):
    event_type = payload.get('event_type')
    event_data = payload.get('data', {})

    logger.info(f"Received event: {event_type} with data: {event_data}")

    if event_type == 'order.confirmed':
        OrderHistoryService.create_history_item(event_data)

    elif event_type in ['delivery.completed', 'order.cancelled']:
        OrderHistoryService.update_order_status(event_data)

    else:
        logger.warning(f"Unhandled event type: {event_type}")
