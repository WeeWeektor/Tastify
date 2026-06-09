import os
from pathlib import Path

import environ
from django.utils.translation import gettext_lazy as _

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DEBUG=(bool, False)
)

environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

SECRET_KEY = env('SECRET_KEY')
DEBUG = env('DEBUG')
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['*'])

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.staticfiles',

    'rest_framework',
    'corsheaders',
    'drf_spectacular',

    'restaurants',
    'menus',
    'promotions',
    'working_hours',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'shared.middleware.language_middleware.GlobalLanguageMiddleware',
    'shared.middleware.rate_limit_middleware.AdvancedRateLimitMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request'
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'
ASGI_APPLICATION = 'core.asgi.application'

DATABASES = {
    'default': env.db('DATABASE_URL')
}

REDIS_URL = env('REDIS_URL')

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'IGNORE_EXCEPTIONS': True,
        }
    }
}
CACHE_TTL = 60 * 15

MINIO_ENDPOINT = env('MINIO_ENDPOINT')
MINIO_PUBLIC_URL = env('MINIO_PUBLIC_URL')
MINIO_ACCESS_KEY = env('MINIO_ROOT_USER')
MINIO_SECRET_KEY = env('MINIO_ROOT_PASSWORD')
MINIO_REGION = env('MINIO_REGION')

JWT_SECRET_KEY = env('JWT_SECRET_KEY')
INTERNAL_SECRET = env('INTERNAL_SECRET')
AUTH_SERVICE_URL = env('AUTH_SERVICE_URL')
MEDIA_SERVICE_URL = env('MEDIA_SERVICE_URL')
BILLING_SERVICE_URL = env('BILLING_SERVICE_URL')

LANGUAGE_CODE = 'en'
LANGUAGES = [
    ('en', _('English')),
    ('uk', _('Ukrainian')),
]
LOCALE_PATHS = [
    str(BASE_DIR / 'locale'),
]
LANGUAGE_COOKIE_NAME = 'django_language'
LANGUAGE_COOKIE_DOMAIN = None
LANGUAGE_COOKIE_PATH = '/'

TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'shared.auth_backend.MicroserviceJWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'UNAUTHENTICATED_USER': None,

    'DEFAULT_PAGINATION_CLASS': 'shared.pagination.BasePageNumberPagination',
    'PAGE_SIZE': 20,
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Tastify restaurant API',
    'DESCRIPTION': 'API for restaurants, menus, promotions, and working hours management.',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

# TODO
GLOBAL_RATE_LIMIT = {}
RATE_LIMITS = {}
