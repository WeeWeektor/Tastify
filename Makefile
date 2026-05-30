DC = docker compose

.PHONY: infra-up infra-down infra-down-volumes infra-ps infra-logs kafka-topics clean help

help:
	@echo "====================================================================="
	@echo "🚀 Tastify Root Commands (Using Compose Include)"
	@echo "====================================================================="
	@echo "Керування всією системою:"
	@echo "  make infra-up            - Запустити абсолютно всі сервіси (infra, gateway, apps)"
	@echo "  make infra-down          - Зупинити всі контейнери"
	@echo "  make infra-down-volumes  - Зупинити все та повністю очистити бази даних (volumes)"
	@echo "  make infra-ps            - Перевірити статус усіх контейнерів та їхній health"
	@echo "  make infra-logs          - Дивитися логи всіх сервісів одночасно"
	@echo ""
	@echo "Робота з конкретним мікросервісом (напр. s=auth_service або s=user_service):"
	@echo "  make logs s=user_service - Логи конкретного контейнера"
	@echo "  make shell s=auth_service- Зайти всередину контейнера (bash)"
	@echo ""
	@echo "Автоматизація:"
	@echo "  make kafka-topics        - Створити всі необхідні топіки в Kafka"
	@echo "  make clean               - Повне скидання Docker системи та кешу"
	@echo "====================================================================="

infra-up:
	$(DC) up -d
	@echo "Чекаємо 10 секунд для ініціалізації інфраструктури..."
	@sleep 10
	$(DC) ps

infra-down:
	$(DC) down

infra-down-volumes:
	$(DC) down -v

infra-ps:
	$(DC) ps

infra-logs:
	$(DC) logs -f

logs:
	$(DC) logs -f $(s)

shell:
	$(DC) exec $(s) /bin/bash

kafka-topics:
	chmod +x infra/kafka/create_topics.sh
	./infra/kafka/create_topics.sh

clean:
	$(DC) down -v
	docker system prune -f