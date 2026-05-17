import logging

from celery import shared_task
from django.utils import timezone

from .models import RefreshTokenBlacklist
from .services.email_service import EmailSenderService, VerificationEmail

logger = logging.getLogger(__name__)


@shared_task
def send_verification_email_task(email: str, token: str):
    """
    Фонова задача для відправки листа.
    """
    logger.info(f"Starting background task to send verification email to {email}")

    email_template = VerificationEmail(to_email=email, token=token)
    success = EmailSenderService.send(email_template)

    if success:
        logger.info(f"Successfully sent verification email to {email}")
    else:
        logger.error(f"Failed to send verification email to {email} via Celery worker")

    return success


@shared_task(name="clean_expired_blacklisted_tokens")
def clean_expired_blacklisted_tokens():
    """
    Видаляє з бази токени, термін дії яких вже вийшов природним шляхом.
    """
    now = timezone.now()

    deleted_count, _ = RefreshTokenBlacklist.objects.filter(expires_at__lt=now).delete()

    if deleted_count > 0:
        logger.info(f"Cleaned up {deleted_count} expired tokens from the blacklist.")

    return deleted_count
