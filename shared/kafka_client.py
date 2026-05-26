import json
import logging
import os

from confluent_kafka import Producer, Consumer, KafkaError

logger = logging.getLogger(__name__)


class KafkaProducerClient:
    """
        Універсальний клієнт для відправки подій у Kafka.
        Інкапсулює логіку підключення, серіалізації в JSON та обробки помилок.
    """
    _instance = None

    def __new__(cls):
        """Реалізація патерну Singleton для забезпечення єдиного екземпляру клієнта."""
        if cls._instance is None:
            cls._instance = super(KafkaProducerClient, cls).__new__(cls)
            cls._instance._initialize_producer()
        return cls._instance

    def _initialize_producer(self):
        bootstrap_servers = os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')

        conf = {
            'bootstrap.servers': bootstrap_servers,
            'client.id': os.environ.get('HOSTNAME', 'tastify-service'),
        }
        self.producer = Producer(conf)

    def _delivery_report(self, err, msg):
        """Внутрішній коллбек, який Kafka викликає після спроби доставки."""
        if err is not None:
            logger.error(f"Failed to deliver message to {msg.topic()}: {err}")
        else:
            logger.info(f"Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")

    def publish(self, topic: str, data: dict):
        """
            Відправляє словник (data) у вказаний Kafka топік.

            :param topic: Назва топіку (напр. 'user.created')
            :param data: Словник з даними події
        """
        try:
            json_data = json.dumps(data).encode('utf-8')

            self.producer.produce(
                topic=topic,
                value=json_data,
                callback=self._delivery_report
            )

            self.producer.poll(0)

        except Exception as e:
            logger.error(f"Error while producing message to Kafka topic {topic}: {e}")
            raise

    def flush(self):
        """Забезпечує відправку всіх накопичених повідомлень перед завершенням роботи."""
        self.producer.flush()


class BaseKafkaConsumer:
    """
        Універсальний клас для читання повідомлень з Kafka.
    """

    def __init__(self, topics: list, group_id: str):
        bootstrap_servers = os.environ.get('KAFKA_BOOTSTRAP_SERVERS')

        self.consumer = Consumer({
            'bootstrap.servers': bootstrap_servers,
            'group.id': group_id,
            'auto.offset.reset': 'earliest',
            'enable.auto.commit': True
        })
        self.consumer.subscribe(topics)
        logger.info(f"Signed up for topics {topics}. Group: {group_id}")

    def start_listening(self, message_handler_callback):
        """
        Запускає безкінечний цикл. При отриманні повідомлення викликає message_handler_callback.
        """
        try:
            while True:
                msg = self.consumer.poll(timeout=1.0)

                if msg is None:
                    continue

                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    else:
                        logger.error(f"Kafka Error: {msg.error()}")
                        break

                try:
                    payload = json.loads(msg.value().decode('utf-8'))

                    message_handler_callback(payload)

                except json.JSONDecodeError:
                    logger.error("Invalid JSON message in Kafka")
                except Exception as e:
                    logger.error(f"Error in the handler: {str(e)}")

        except KeyboardInterrupt:
            logger.info("Consumer stop...")
        finally:
            self.consumer.close()
