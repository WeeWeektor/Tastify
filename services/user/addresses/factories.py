import uuid

import factory
from factory.django import DjangoModelFactory

from .models import DeliveryAddress


class DeliveryAddressFactory(DjangoModelFactory):
    """
        Фабрика для генерації реалістичних фейкових адрес доставки.
        Використовується для тестів та сідінгу (наповнення) бази даних.
    """

    class Meta:
        model = DeliveryAddress

    id = factory.LazyFunction(uuid.uuid4)
    user_id = factory.LazyFunction(uuid.uuid4)
    label = factory.Iterator(['Дім', 'Робота', 'Батьки', 'Квартира дівчини', '', '', ''])
    address_line = factory.Faker('street_address', locale='uk_UA')
    city = factory.Faker('city', locale='uk_UA')
    latitude = factory.Faker(
        'pyfloat',
        left_digits=2,
        right_digits=6,
        min_value=-90.0,
        max_value=90.0
    )
    longitude = factory.Faker(
        'pyfloat',
        left_digits=3,
        right_digits=6,
        min_value=-180.0,
        max_value=180.0
    )
    apartment = factory.Faker('building_number')
    entrance = factory.Faker('random_int', min=1, max=10)
    floor = factory.Faker('random_int', min=1, max=25)
    comment = factory.Maybe(
        'step',
        yes_declaration=factory.Faker('sentence', locale='uk_UA'),
        no_declaration=''
    )
    is_default = False
