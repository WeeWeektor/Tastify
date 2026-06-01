from django.conf import settings
from rest_framework import serializers

from shared import validate_no_xss, validate_phone
from .models import CustomerProfile


class CustomerProfileSerializer(serializers.ModelSerializer):
    display_name = serializers.CharField(max_length=100, validators=[validate_no_xss])
    first_name = serializers.CharField(max_length=150, allow_blank=True, validators=[validate_no_xss])
    last_name = serializers.CharField(max_length=150, allow_blank=True, validators=[validate_no_xss])
    phone = serializers.CharField(max_length=20, allow_blank=True, allow_null=True, validators=[validate_phone])
    notification_telegram = serializers.CharField(
        max_length=100,
        allow_blank=True,
        allow_null=True,
        validators=[validate_no_xss]
    )
    language = serializers.ChoiceField(
        choices=settings.LANGUAGES,
        write_only=True,
        required=False
    )

    class Meta:
        model = CustomerProfile
        fields = [
            'user_id',
            'display_name',
            'first_name',
            'last_name',
            'phone',
            'avatar_url',
            'bonus_points',
            'notification_telegram',
            'created_at',
            'updated_at',
            'language'
        ]

        read_only_fields = [
            'user_id',
            'bonus_points',
            'created_at',
            'updated_at'
        ]
