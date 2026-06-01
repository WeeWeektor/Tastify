from favorites.models import FavoriteRestaurant


class FavoriteRestaurantService:
    @classmethod
    def add_favorite_restaurant(cls, user_id: str, validated_data: dict) -> FavoriteRestaurant:
        return FavoriteRestaurant.objects.create(user_id=user_id, **validated_data)

    @classmethod
    def remove_favorite_restaurant(cls, instance: FavoriteRestaurant) -> None:
        instance.delete()
