#!/bin/bash

KAFKA_CONTAINER="tastify_kafka"
BOOTSTRAP="localhost:9092"

echo "Чекаємо поки Kafka буде готова..."
sleep 5

create_topic() {
  local TOPIC=$1
  local PARTITIONS=${2:-3}
  echo "Створюємо топік: $TOPIC"
  docker exec $KAFKA_CONTAINER \
    kafka-topics --bootstrap-server $BOOTSTRAP \
    --create \
    --topic $TOPIC \
    --partitions $PARTITIONS \
    --replication-factor 1 \
    --if-not-exists
}

# Saga flow
create_topic "order.created"
create_topic "payment.success"
create_topic "payment.failed"
create_topic "order.confirmed"
create_topic "order.cancelled"

# Restaurant flow
create_topic "order.preparing"
create_topic "order.ready_for_pickup"

# Delivery flow
create_topic "delivery.assigned"
create_topic "delivery.picked_up"
create_topic "delivery.completed"
create_topic "courier.location_updated" 6

# Reviews
create_topic "review.created"

# Billing
create_topic "subscription.activated"
create_topic "subscription.expired"
create_topic "commission.created"

echo ""
echo "Список створених топіків:"
docker exec $KAFKA_CONTAINER \
  kafka-topics --bootstrap-server $BOOTSTRAP --list

echo "Готово!"