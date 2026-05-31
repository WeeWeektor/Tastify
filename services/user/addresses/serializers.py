from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from .models import DeliveryAddress


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryAddress
        fields = [
            'id',
            'user_id',
            'label',
            'address_line',
            'city',
            'latitude',
            'longitude',
            'apartment',
            'entrance',
            'floor',
            'comment',
            'is_default',
            'created_at',
            'updated_at'
        ]

        read_only_fields = [
            'id',
            'user_id',
            'created_at',
            'updated_at'
        ]

    def validate(self, attrs):
        label = attrs.get('label')

        if label:
            request = self.context.get('request')
            user_id = getattr(request.user, 'id', None) if request and hasattr(request, 'user') else None

            if user_id:
                instance_id = self.instance.id if self.instance else None
                query = DeliveryAddress.objects.filter(user_id=user_id, label=label)

                if instance_id:
                    query = query.exclude(id=instance_id)

                if query.exists():
                    raise serializers.ValidationError({
                        "label": _("An address with this label already exists.")
                    })

        return attrs
