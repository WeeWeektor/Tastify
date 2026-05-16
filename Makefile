.PHONY: infra-up infra-down infra-logs kafka-topics infra-ps clean

infra-up:
	docker compose -f docker-compose.yml up -d
	@echo "Чекаємо поки всі сервіси піднімуться..."
	@sleep 10
	@docker compose -f docker-compose.yml ps

infra-down:
	docker compose -f docker-compose.yml down

infra-down-volumes:
	docker compose -f docker-compose.yml down -v

infra-ps:
	docker compose -f docker-compose.yml ps

infra-logs:
	docker compose -f docker-compose.yml logs -f

kafka-topics:
	chmod +x infra/kafka/create_topics.sh
	./infra/kafka/create_topics.sh

clean:
	docker compose -f docker-compose.yml down -v
	docker system prune -f