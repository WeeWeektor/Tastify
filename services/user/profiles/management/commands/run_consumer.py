from django.core.management.base import BaseCommand

from profiles.events import handle_user_events
from shared.kafka_client import BaseKafkaConsumer


class Command(BaseCommand):
    help = "Run Kafka consumer for User Service"

    def handle(self, *args, **options):
        consumer = BaseKafkaConsumer(
            topics=['user.created'],
            group_id='user_service_group'
        )

        self.stdout.write(self.style.SUCCESS('Starting consumer events for user service...'))

        consumer.start_listening(message_handler_callback=handle_user_events)
