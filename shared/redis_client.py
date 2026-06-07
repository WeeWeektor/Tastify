import redis


class BaseRedisService:
    """
    Базовий сервіс для роботи з ключами в Redis.
    """

    def __init__(self, redis_url: str, prefix: str, ttl_seconds: int = 24 * 3600) -> None:
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.prefix = prefix
        self.ttl = ttl_seconds

    def _get_key(self, key: str) -> str:
        return f"{self.prefix}:{key}"

    def store(self, value: str, key: str) -> None:
        """
        Зберігає значення в Redis.
        """
        self.redis_client.set(name=self._get_key(key), value=str(value), ex=self.ttl)

    def get_value(self, key: str) -> str | None:
        """
        Отримує значення з Redis.
        """
        return self.redis_client.get(self._get_key(key))

    def delete(self, key: str) -> None:
        """
        Видаляє ключ з Redis.
        """
        self.redis_client.delete(self._get_key(key))

    def delete_by_pattern(self, pattern_key: str) -> None:
        """
        Видаляє всі ключі, які відповідають патерну.
        Використовується для інвалідації всіх сторінок пагінації користувача.
        """
        match_pattern = f"{self.prefix}:{pattern_key}*"
        keys_to_delete = list(self.redis_client.scan_iter(match=match_pattern))

        if keys_to_delete:
            self.redis_client.delete(*keys_to_delete)
