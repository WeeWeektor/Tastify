from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from menus.models import Product, MenuCategory, MenuItem, ModifierGroup, ModifierOption
from shared.validators import validate_no_xss


class ManagementProductSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=200, validators=[validate_no_xss])
    description = serializers.CharField(required=False, allow_blank=True, validators=[validate_no_xss])

    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ['id', 'restaurant']

    def validate_allergens(self, value):
        """Перевіряємо кожен елемент списку алергенів на XSS"""
        if isinstance(value, list):
            for item in value:
                validate_no_xss(str(item))
        return value

    def validate_ingredients(self, value):
        """Перевіряємо кожен елемент списку інгредієнтів на XSS"""
        if isinstance(value, list):
            for item in value:
                validate_no_xss(str(item))
        return value

    def validate(self, attrs):
        weight = attrs.get('weight_grams')
        calories = attrs.get('calories')

        if weight is not None and weight < 0:
            raise serializers.ValidationError({"weight_grams": _("Weight cannot be negative.")})

        if calories is not None and calories < 0:
            raise serializers.ValidationError({"calories": _("Calories cannot be negative.")})

        return attrs


class ManagementMenuCategorySerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=100, validators=[validate_no_xss])

    class Meta:
        model = MenuCategory
        fields = '__all__'
        read_only_fields = ['id', 'restaurant']


class ManagementModifierOptionSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=100, validators=[validate_no_xss])

    class Meta:
        model = ModifierOption
        fields = '__all__'
        read_only_fields = ['id', 'group']

    def validate_extra_price(self, value):
        if value < 0:
            raise serializers.ValidationError(_("The additional price cannot be negative."))
        return value


class ManagementModifierGroupSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=100, validators=[validate_no_xss])
    options = ManagementModifierOptionSerializer(many=True, read_only=True)

    class Meta:
        model = ModifierGroup
        fields = '__all__'
        read_only_fields = ['id', 'menu_item']

    def validate(self, attrs):
        min_sel = attrs.get('min_selections', getattr(self.instance, 'min_selections', 0))
        max_sel = attrs.get('max_selections', getattr(self.instance, 'max_selections', 1))

        if min_sel < 0:
            raise serializers.ValidationError({"min_selections": _("The minimum cannot be less than 0.")})

        if min_sel > max_sel:
            raise serializers.ValidationError({
                "min_selections": _("The minimum number of elections cannot exceed the maximum.")
            })

        return attrs


class ManagementMenuItemSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=200, validators=[validate_no_xss])
    modifier_groups = ManagementModifierGroupSerializer(many=True, read_only=True)

    class Meta:
        model = MenuItem
        fields = '__all__'
        read_only_fields = ['id', 'category']

    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError(_("The price cannot be negative."))
        return value

    def validate_prep_time_minutes(self, value):
        if value < 0:
            raise serializers.ValidationError(_("Cooking time cannot be negative."))
        return value
