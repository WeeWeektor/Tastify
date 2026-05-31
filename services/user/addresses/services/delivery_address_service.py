from addresses.models import DeliveryAddress


class DeliveryAddressService:
    @classmethod
    def create_address(cls, user_id: str, validated_data: dict) -> DeliveryAddress:
        address = DeliveryAddress(user_id=user_id, **validated_data)
        address.save()
        return address

    @classmethod
    def update_address(cls, instance: DeliveryAddress, validated_data: dict) -> DeliveryAddress:
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
