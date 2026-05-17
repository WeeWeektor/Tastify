import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.base')

app = Celery('auth_service')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

app.conf.beat_schedule = {
    'cleanup-blacklisted-tokens-every-night': {
        'task': 'clean_expired_blacklisted_tokens',
        'schedule': crontab(hour=3, minute=0),
    },
}
