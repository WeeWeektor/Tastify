import logging

from .services import CustomerProfileService

logger = logging.getLogger(__name__)


def handle_user_events(payload: dict):
    """
        Ця функція приймає JSON з Kafka і вирішує, що з ним робити.
    """
    event_type = payload.get('event_type')
    event_data = payload.get('data', {})

    logger.info(f"Received event: {event_type} with data: {event_data}")

    if event_type == 'user_registered':
        role = event_data.get('role')

        if role == 'consumer':
            CustomerProfileService.create_profile_from_event(event_data)
        else:
            logger.info(f"Ignoring user_registered event for role: {role}")

    elif event_type == 'user_deleted':
        # TODO - implement user deletion handling
        pass

    else:
        logger.warning(f"Unhandled event type: {event_type}")
