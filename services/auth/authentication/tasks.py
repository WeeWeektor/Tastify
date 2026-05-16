import logging

from celery import shared_task

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
