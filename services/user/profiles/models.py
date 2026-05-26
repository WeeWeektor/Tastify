import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _


class CustomerProfile(models.Model):
    user_id = models.UUIDField(
        _('User ID'),
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text=_("Unique identifier from the Auth Service.")
    )
    display_name = models.CharField(_('Display Name'), max_length=100)
    first_name = models.CharField(_('first name'), max_length=150, blank=True)
    last_name = models.CharField(_('last name'), max_length=150, blank=True)
    phone = models.CharField(
        _('Phone Number'),
        max_length=20,
        null=True,
        blank=True,
        unique=True,
        help_text=_("Contact phone number for couriers. Must be unique.")
    )
    avatar_url = models.URLField(_('Avatar URL'), null=True, blank=True)
    bonus_points = models.PositiveIntegerField(_('Bonus Points'), default=0)
    notification_telegram = models.CharField(
        _('Telegram Username'),
        max_length=100,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    objects = models.Manager()

    class Meta:
        db_table = 'customer_profiles'
        verbose_name = _('Customer Profile')
        verbose_name_plural = _('Customer Profiles')
        ordering = ['-created_at']

        default_permissions = ()

        indexes = [
            models.Index(fields=['phone'], name='idx_customer_phone'),
            models.Index(fields=['notification_telegram'], name='idx_customer_telegram'),
            models.Index(fields=['created_at'], name='idx_customer_created_at'),
        ]

    def __str__(self):
        return f"{self.display_name} ({self.user_id})"
