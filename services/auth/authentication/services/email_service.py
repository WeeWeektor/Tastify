import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

from django.conf import settings
from django.core.mail import send_mail

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
        subject = 'Підтвердження реєстрації на Tastify'

        message = (
            f"Вітаємо на Tastify!\n\n"
            f"Для завершення реєстрації та активації акаунту перейдіть за посиланням:\n"
            f"{link}\n\n"
            f"Це посилання дійсне протягом 24 годин.\n"
            f"Якщо ви не реєструвалися на нашому сайті, просто проігноруйте цей лист."
        )

        html_message = f"""
        <html>
            <body>
                <h2>Вітаємо на Tastify! 🍔</h2>
                <p>Для завершення реєстрації та активації акаунту натисніть на кнопку нижче:</p>
                <a href="{link}" style="display: inline-block; padding: 10px 20px; background-color: #ff4500; color: white; text-decoration: none; border-radius: 5px;">
                    Підтвердити Email
                </a>
                <p><small>Це посилання дійсне протягом 24 годин.</small></p>
            </body>
        </html>
        """

        return EmailPayload(
            subject=subject,
            message=message,
            html_message=html_message,
            recipients=[self.to_email]
        )


class PasswordResetEmail(BaseEmailTemplate):
    def __init__(self, to_email: str, reset_code: str):
        super().__init__(to_email)
        self.reset_code = reset_code

    def generate(self) -> EmailPayload:
        # TODO - реалізувати генерацію листа для скидання пароля
        pass


class EmailSenderService:
    """
    Єдина точка входу для відправки будь-яких листів.
    """

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
