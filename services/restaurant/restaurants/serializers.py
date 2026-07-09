from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from shared.validators import validate_no_xss, validate_phone
from .models import Restaurant, RestaurantEmployee, EmployeeRole


class RestaurantSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=200, validators=[validate_no_xss])
    description = serializers.CharField(allow_blank=True, required=False, validators=[validate_no_xss])
    address = serializers.CharField(max_length=255, validators=[validate_no_xss])
    city = serializers.CharField(max_length=100, validators=[validate_no_xss])
    phone = serializers.CharField(max_length=20, validators=[validate_phone])
    legal_name = serializers.CharField(max_length=200, allow_blank=True, required=False, validators=[validate_no_xss])
    tax_id = serializers.CharField(max_length=50, allow_blank=True, required=False, validators=[validate_no_xss])
    cuisine_types = serializers.ListField(
        child=serializers.CharField(max_length=50, validators=[validate_no_xss]),
        allow_empty=True,
        required=False,
        help_text=_("List of cuisine types, e.g., ['pizza', 'sushi']")
    )

    class Meta:
        model = Restaurant
        fields = '__all__'

        read_only_fields = [
            'id',
            'slug',
            'rating',
            'rating_count',
            'is_active',
            'is_open',
            'commission_rate',
            'is_promoted',
            'promotion_expires_at',
            'created_at',
            'updated_at'
        ]


class RestaurantEmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = RestaurantEmployee
        fields = [
            'id',
            'restaurant',
            'user_id',
            'role',
            'is_active',
            'created_at'
        ]

        read_only_fields = [
            'id',
            'created_at',
            'restaurant'
        ]

    def validate(self, attrs):
        request = self.context.get('request')
        view = self.context.get('view')
        restaurant_slug = view.kwargs.get('slug') if view else None

        target_role = attrs.get('role', getattr(self.instance, 'role', None))

        if request and restaurant_slug and target_role:
            current_user_id = getattr(request.user, 'id', None)
            if not current_user_id and hasattr(request, 'user_context'):
                current_user_id = request.user_context.get('user_id')

            current_employee = RestaurantEmployee.objects.filter(
                restaurant__slug=restaurant_slug,
                user_id=current_user_id
            ).first()

            if current_employee:
                if current_employee.role == EmployeeRole.MANAGER:
                    if target_role in [EmployeeRole.OWNER, EmployeeRole.MANAGER]:
                        raise serializers.ValidationError({
                            "role": _("Only the Owner (OWNER) can assign the roles of MANAGER or OWNER.")
                        })

        if target_role == EmployeeRole.OWNER and restaurant_slug:
            existing_owner_query = RestaurantEmployee.objects.filter(
                restaurant__slug=restaurant_slug,
                role=EmployeeRole.OWNER
            )

            if self.instance:
                existing_owner_query = existing_owner_query.exclude(pk=self.instance.pk)

            if existing_owner_query.exists():
                raise serializers.ValidationError({
                    "role": _("This restaurant already has an owner. You cannot assign more than one OWNER.")
                })

        return attrs
