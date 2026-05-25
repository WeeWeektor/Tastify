import re

from rest_framework import serializers

from .models import CustomerProfile


class CustomerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerProfile
        fields = [
            'user_id',
            'display_name',
            'phone',
            'avatar_url',
            'bonus_points',
            'notification_telegram',
            'created_at',
            'updated_at'
        ]

        read_only_fields = [
            'user_id',
            'bonus_points',
            'created_at',
            'updated_at'
        ]

    @staticmethod
    def validate_phone(value):
        if value:
            cleaned_value = re.sub(r'[\s\-()]+', '', value)

            if not re.match(r'^\+?\d{10,15}$', cleaned_value):
                raise serializers.ValidationError("Invalid phone number format.")
            return cleaned_value
        return value
