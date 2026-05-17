import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

from django.conf import settings
from django.core.mail import send_mail
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


@dataclass
class EmailPayload:
    subject: str
    message: str
    html_message: str
    recipients: list[str]


class BaseEmailTemplate(ABC):
    def __init__(self, to_email: str):
        self.to_email = to_email

    @abstractmethod
    def generate(self) -> EmailPayload:
        pass


class VerificationEmail(BaseEmailTemplate):
    """Генератор контенту для листа підтвердження пошти."""

    def __init__(self, to_email: str, token: str):
        super().__init__(to_email)
        self.token = token

    def generate(self) -> EmailPayload:
        link = f"{settings.FRONTEND_URL}/verify-email?token={self.token}"
        subject = _('Registration Confirmation at Tastify')

        message = _(
            "Welcome to Tastify!\n\n"
            "To complete your registration and activate your account, please follow the link:\n"
            "{link}\n\n"
            "This link is valid for 24 hours.\n"
            "If you did not register on our site, please ignore this email."
        ).format(link=link)

        html_message = f"""
        <html>
            <body>
                <h2>{_("Welcome to Tastify! 🍔")}</h2>
                <p>{_("To complete your registration and activate your account, click the button below:")}</p>
                <a href="{link}" style="display: inline-block; padding: 10px 20px; background-color: #ff4500; color: white; text-decoration: none; border-radius: 5px;">
                    {_("Confirm Email")}
                </a>
                <p><small>{_("This link is valid for 24 hours.")}</small></p>
            </body>
        </html>
        """

        return EmailPayload(
            subject=str(subject),
            message=str(message),
            html_message=html_message,
            recipients=[self.to_email]
        )


class PasswordResetEmail(BaseEmailTemplate):
    """Генератор контенту для листа скидання пароля."""

    def __init__(self, to_email: str, reset_token: str):
        super().__init__(to_email)
        self.reset_token = reset_token

    def generate(self) -> EmailPayload:
        link = f"{settings.FRONTEND_URL}/reset-password?token={self.reset_token}"
        subject = _('Password Reset at Tastify')

        message = _(
            "You received this email because a password reset request was made for your Tastify account.\n\n"
            "To set a new password, please follow the link:\n"
            "{link}\n\n"
            "This link is valid for 1 hour.\n"
            "If you did not request this, please ignore this email; your password will remain unchanged."
        ).format(link=link)

        html_message = f"""
        <html>
            <body>
                <h2>{_("Password Reset 🍔")}</h2>
                <p>{_("To set a new password, click the button below:")}</p>
                <a href="{link}" style="display: inline-block; padding: 10px 20px; background-color: #ff4500; color: white; text-decoration: none; border-radius: 5px;">
                    {_("Reset Password")}
                </a>
                <p><small>{_("This link is valid for 1 hour.")}</small></p>
            </body>
        </html>
        """

        return EmailPayload(
            subject=str(subject),
            message=str(message),
            html_message=html_message,
            recipients=[self.to_email]
        )


class EmailSenderService:
    """Єдина точка входу для відправки будь-яких листів."""

    @staticmethod
    def send(template: BaseEmailTemplate) -> bool:
        payload = template.generate()

        try:
            send_mail(
                subject=payload.subject,
                message=payload.message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=payload.recipients,
                html_message=payload.html_message,
                fail_silently=False,
            )
            logger.info(f"Email '{payload.subject}' successfully sent to {payload.recipients}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {payload.recipients}: {str(e)}")
            return False
