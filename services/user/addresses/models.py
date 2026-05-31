import uuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models, transaction
from django.db.models import Q
from django.utils.translation import gettext_lazy as _


class DeliveryAddress(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(
        _('User ID'),
        editable=False,
        db_index=True,
        help_text=_("Unique identifier from the Auth Service.")
    )

    label = models.CharField(
        _('Label'),
        max_length=50,
        blank=True,
        default='',
        help_text=_("For example: 'Home', 'Work', etc.")
    )
    address_line = models.CharField(_('Address Line'), max_length=255)
    city = models.CharField(_('City'), max_length=100)

    latitude = models.FloatField(
        _('Latitude'),
        validators=[MinValueValidator(-90.0), MaxValueValidator(90.0)]
    )
    longitude = models.FloatField(
        _('Longitude'),
        validators=[MinValueValidator(-180.0), MaxValueValidator(180.0)]
    )

    apartment = models.CharField(_('Apartment/Unit'), max_length=20, blank=True, default='')
    entrance = models.CharField(_('Entrance'), max_length=10, blank=True, default='')
    floor = models.SmallIntegerField(_('Floor'), null=True, blank=True)
    comment = models.TextField(_('Comment'), blank=True, default='')
    is_default = models.BooleanField(_('Is Default'), default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()

    class Meta:
        db_table = 'delivery_addresses'
        verbose_name = _('Delivery Address')
        verbose_name_plural = _('Delivery Addresses')
        ordering = ['-is_default', '-created_at']

        default_permissions = ()

        indexes = [
            models.Index(fields=['user_id', 'is_default']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['user_id'],
                condition=Q(is_default=True),
                name='unique_default_address_per_user'
            ),
            models.UniqueConstraint(
                fields=['user_id', 'label'],
                condition=~Q(label=''),
                name='unique_label_per_user'
            )
        ]

    def __str__(self):
        prefix = self.label if self.label else _("Address")
        return f"{prefix} - {self.address_line}"

    def save(self, *args, **kwargs):
        if self.is_default:
            with transaction.atomic():
                DeliveryAddress.objects.filter(
                    user_id=self.user_id,
                    is_default=True
                ).exclude(pk=self.pk).update(is_default=False)

                super().save(*args, **kwargs)
        else:
            if not self.pk and not DeliveryAddress.objects.filter(user_id=self.user_id).exists():
                self.is_default = True

            super().save(*args, **kwargs)
