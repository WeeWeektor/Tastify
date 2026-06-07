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

    'profiles',
    'addresses',
    'favorites',
    'order_history',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'shared.GlobalLanguageMiddleware',
    'shared.AdvancedRateLimitMiddleware',
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
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
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

MINIO_ENDPOINT = os.environ.get('MINIO_ENDPOINT')
MINIO_PUBLIC_URL = os.environ.get('MINIO_PUBLIC_URL')
MINIO_ACCESS_KEY = os.environ.get('MINIO_ROOT_USER')
MINIO_SECRET_KEY = os.environ.get('MINIO_ROOT_PASSWORD')
MINIO_REGION = os.environ.get('MINIO_REGION')

JWT_SECRET_KEY = env('JWT_SECRET_KEY')
INTERNAL_SECRET = env('INTERNAL_SECRET')
AUTH_SERVICE_URL = env('AUTH_SERVICE_URL')
ANALYTICS_SERVICE_URL = env('ANALYTICS_SERVICE_URL')

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

    'DEFAULT_PAGINATION_CLASS': 'shared.BasePageNumberPagination',
    'PAGE_SIZE': 20,
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Tastify User API',
    'DESCRIPTION': 'API for user profiles, addresses, favorites, and order history',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

GLOBAL_RATE_LIMIT = {'rate': 100, 'period': 60}
RATE_LIMITS = {
    '/api/v1/users/me/': {'rate': 20, 'period': 60},
    '/api/v1/users/me/orders/': {'rate': 15, 'period': 60},
    '/api/v1/users/addresses/': {'rate': 15, 'period': 60},
    '/api/v1/users/favorites/': {'rate': 20, 'period': 60},
}
