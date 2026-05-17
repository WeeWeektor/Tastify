import uuid

from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.db.models import Q, F


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('Email must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))

        return self.create_user(email, password, **extra_fields)


ROLE_CHOICES = [
    ('customer', _('Customer')),
    ('restaurant', _('Restaurant Owner')),
    ('courier', _('Courier')),
    ('admin', _('Admin')),
]


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_('email address'), unique=True, max_length=100)
    role = models.CharField(_('role'), max_length=20, choices=ROLE_CHOICES, default='customer')

    first_name = models.CharField(_('first name'), max_length=150, blank=True)
    last_name = models.CharField(_('last name'), max_length=150, blank=True)

    is_verified = models.BooleanField(
        _('verified'),
        default=False,
        help_text=_('Designates whether the user has verified their email address.')
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_('Designates whether this user should be treated as active. '
                    'Unselect this instead of deleting accounts.')
    )
    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Designates whether the user can log into this admin site.')
    )

    created_at = models.DateTimeField(_('date joined'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    last_login_ip = models.GenericIPAddressField(
        _('last login IP'),
        null=True,
        blank=True
    )

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        db_table = 'users'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['role'], name='role_idx'),
        ]
        permissions = [
            ("can_suspend_user", _("Can suspend users from the platform")),
        ]

    def __str__(self):
        return self.email


class RefreshTokenBlacklist(models.Model):
    """
    Модель для зберігання заблокованих refresh токенів.
    """
    id = models.BigAutoField(primary_key=True, editable=False)
    jti = models.CharField(_('refresh token'), max_length=36, unique=True)
    user_id = models.UUIDField(_('user id'), db_index=True)

    blacklisted_at = models.DateTimeField(_('blacklisted at'), auto_now_add=True)
    expires_at = models.DateTimeField(_('expires at'), db_index=True)

    objects = models.Manager()

    class Meta:
        verbose_name = _('blacklisted refresh token')
        verbose_name_plural = _('blacklisted refresh tokens')
        db_table = 'blacklisted_refresh_tokens'
        ordering = ['-blacklisted_at']
        get_latest_by = 'blacklisted_at'
        constraints = [
            models.CheckConstraint(
                check=Q(expires_at__gt=F('blacklisted_at')),
                name='check_expires_after_blacklisting'
            ),
        ]

    def __str__(self):
        return f"Blacklisted Token {self.jti} (User: {self.user_id})"
