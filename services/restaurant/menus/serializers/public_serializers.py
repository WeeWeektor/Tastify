from rest_framework import serializers

from menus.models import MenuCategory, MenuItem, ModifierGroup, ModifierOption


class PublicModifierOptionSerializer(serializers.ModelSerializer):
    """Серіалізатор для опцій (наприклад: '30 см', 'Подвійний сир')"""

    class Meta:
        model = ModifierOption
        fields = ['id', 'name', 'extra_price']


class PublicModifierGroupSerializer(serializers.ModelSerializer):
    """Серіалізатор для груп модифікаторів (наприклад: 'Оберіть розмір')"""
    options = PublicModifierOptionSerializer(many=True, read_only=True)

    class Meta:
        model = ModifierGroup
        fields = ['id', 'name', 'is_required', 'min_selections', 'max_selections', 'options']


class PublicMenuItemSerializer(serializers.ModelSerializer):
    """Серіалізатор для страв. Витягує фізичні властивості з Product."""
    modifiers = PublicModifierGroupSerializer(source='modifier_groups', many=True, read_only=True)

    description = serializers.SerializerMethodField()
    weight_grams = serializers.SerializerMethodField()
    calories = serializers.SerializerMethodField()
    allergens = serializers.SerializerMethodField()
    ingredients = serializers.SerializerMethodField()
    is_spicy = serializers.SerializerMethodField()
    is_vegetarian = serializers.SerializerMethodField()
    is_vegan = serializers.SerializerMethodField()

    class Meta:
        model = MenuItem
        fields = [
            'id', 'name', 'price', 'image_url', 'prep_time_minutes',
            'description', 'weight_grams', 'calories', 'allergens',
            'ingredients', 'is_spicy', 'is_vegetarian', 'is_vegan',
            'modifiers'
        ]

    def get_description(self, obj):
        return obj.base_product.description if obj.base_product else ""

    def get_weight_grams(self, obj):
        return obj.base_product.weight_grams if obj.base_product else None

    def get_calories(self, obj):
        return obj.base_product.calories if obj.base_product else None

    def get_allergens(self, obj):
        return obj.base_product.allergens if obj.base_product else []

    def get_ingredients(self, obj):
        return obj.base_product.ingredients if obj.base_product else []

    def get_is_spicy(self, obj):
        return obj.base_product.is_spicy if obj.base_product else False

    def get_is_vegetarian(self, obj):
        return obj.base_product.is_vegetarian if obj.base_product else False

    def get_is_vegan(self, obj):
        return obj.base_product.is_vegan if obj.base_product else False


class PublicMenuCategorySerializer(serializers.ModelSerializer):
    """Головний серіалізатор: Категорія -> Страви -> Модифікатори"""
    items = PublicMenuItemSerializer(many=True, read_only=True)

    class Meta:
        model = MenuCategory
        fields = ['id', 'name', 'items']
