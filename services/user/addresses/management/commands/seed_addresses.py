from django.core.management.base import BaseCommand

from addresses.factories import DeliveryAddressFactory


class Command(BaseCommand):
    help = 'Генерує фейкові адреси для тестування'

    def handle(self, *args, **kwargs):
        user_id = "07570f93-7137-416f-b638-442aa6deada0"

        self.stdout.write("Починаємо генерацію адрес...")

        DeliveryAddressFactory(user_id=user_id, is_default=True)
        DeliveryAddressFactory.create_batch(5, user_id=user_id)

        self.stdout.write(self.style.SUCCESS('Успішно створено 1 дефолтну та 5 звичайних адрес!'))
