import redis
from django.conf import settings


class RedisTokenService:
    """
    Сервіс для роботи з токенами в Redis.
    """

    def __init__(self, prefix: str, ttl_seconds: int = 24 * 3600) -> None:
        self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        self.prefix = prefix
        self.ttl = ttl_seconds

    def _get_key(self, token: str) -> str:
        return f"{self.prefix}:{token}"

    def store(self, user_id: str, token: str) -> None:
        self.redis_client.set(name=self._get_key(token), value=str(user_id), ex=self.ttl)

    def get_user_id_from_verification_token(self, token: str) -> str | None:
        return self.redis_client.get(self._get_key(token))

    def delete(self, token: str) -> None:
        self.redis_client.delete(self._get_key(token))


email_verification_service = RedisTokenService(prefix="email_verification", ttl_seconds=24 * 3600)
password_reset_service = RedisTokenService(prefix="password_reset", ttl_seconds=3600)
