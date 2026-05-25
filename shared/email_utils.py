from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class EmailPayload:
    """Контейнер для даних електронного листа."""
    subject: str
    message: str
    html_message: str
    recipients: list[str]


class BaseEmailTemplate(ABC):
    """Базовий клас для створення шаблонів листів."""

    def __init__(self, to_email: str):
        self.to_email = to_email

    @abstractmethod
    def generate(self) -> EmailPayload:
        pass
