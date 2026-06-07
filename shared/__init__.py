from .ip_utils import get_client_ip
from .redis_client import BaseRedisService
from .email_utils import BaseEmailTemplate, EmailPayload
from .validators import validate_no_xss, validate_image, validate_phone
from .kafka_client import KafkaProducerClient, BaseKafkaConsumer
from .minio_client import get_minio_service
from .auth_backend import MicroserviceJWTAuthentication
from .pagination import BasePageNumberPagination

from .middleware.language_middleware import GlobalLanguageMiddleware
from .middleware.rate_limit_middleware import AdvancedRateLimitMiddleware
from .middleware.jwt_auth_middleware import JWTAuthMiddleware

__all__ = [
    "get_client_ip",
    "BaseRedisService",
    "BaseEmailTemplate",
    "EmailPayload",
    "validate_no_xss",
    "validate_image",
    "validate_phone",
    "KafkaProducerClient",
    "BaseKafkaConsumer",
    "get_minio_service",
    "MicroserviceJWTAuthentication",
    "BasePageNumberPagination",

    "GlobalLanguageMiddleware",
    "AdvancedRateLimitMiddleware",
    "JWTAuthMiddleware",
]
