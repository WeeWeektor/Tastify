import uuid

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from slugify import slugify


class Restaurant(models.Model):
    id = models.UUIDField(_("Restaurant ID"), primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(_("Name"), max_length=200)
    slug = models.SlugField(_("Slug"), max_length=250, unique=True, blank=True)
    description = models.TextField(_("Description"), blank=True)

    logo_url = models.URLField(_("Logo URL"), max_length=500, null=True, blank=True)
    cover_url = models.URLField(_("Cover URL"), max_length=500, null=True, blank=True)

    address = models.CharField(_("Physical Address"), max_length=255)
    city = models.CharField(_("City"), max_length=100, db_index=True)
    latitude = models.FloatField(_("Latitude"), validators=[MinValueValidator(-90.0), MaxValueValidator(90.0)])
    longitude = models.FloatField(_("Longitude"), validators=[MinValueValidator(-180.0), MaxValueValidator(180.0)])

    phone = models.CharField(_("Contact Phone"), max_length=20, unique=True)

    cuisine_types = models.JSONField(
        _("Cuisine Types"),
        default=list,
        help_text="List of strings, e.g., ['pizza', 'sushi']"
    )

    min_order_amount = models.DecimalField(_("Minimum Order Amount"), validators=[MinValueValidator(0.0)], max_digits=8,
                                           decimal_places=2, default=0.00)
    delivery_fee = models.DecimalField(_("Delivery Fee"), validators=[MinValueValidator(0.0)], max_digits=6,
                                       decimal_places=2, default=0.00)
    avg_delivery_time = models.SmallIntegerField(_("Average Delivery Time (mins)"), default=30)
    avg_prep_time = models.SmallIntegerField(_("Average Prep Time (mins)"), default=15,
                                             help_text="Used for ML ETA prediction")

    rating = models.DecimalField(_("Rating"), validators=[MinValueValidator(0.0), MaxValueValidator(5.0)], max_digits=3,
                                 decimal_places=2, default=0.00)
    rating_count = models.PositiveIntegerField(_("Rating Count"), default=0)

    is_active = models.BooleanField(_("Is Active"), default=False, help_text="Activated by platform admin")
    is_open = models.BooleanField(_("Is Open Now"), default=False, help_text="Auto-updated based on working hours")
    is_accepting_orders = models.BooleanField(_("Accepting Orders"), default=True,
                                              help_text="Manual toggle to temporarily stop receiving orders")

    legal_name = models.CharField(_("Legal Name"), max_length=200, blank=True, help_text="For billing and payouts")
    tax_id = models.CharField(_("Tax ID"), max_length=50, blank=True, help_text="For official reports")
    commission_rate = models.DecimalField(_("Commission Rate (%)"), validators=[MinValueValidator(0.0)], max_digits=4,
                                          decimal_places=2, default=20.00)

    is_promoted = models.BooleanField(_("Is Promoted"), default=False)
    promotion_expires_at = models.DateTimeField(_("Promotion Expires At"), null=True, blank=True)

    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    objects = models.Manager()

    class Meta:
        db_table = "restaurants"
        verbose_name = _("Restaurant")
        verbose_name_plural = _("Restaurants")
        ordering = ['-created_at']

        indexes = [
            models.Index(fields=['city', 'is_active', 'is_open']),
            models.Index(fields=['city', 'name']),
            models.Index(fields=['-rating']),
        ]

        constraints = [
            models.CheckConstraint(
                condition=models.Q(rating__gte=0.0) & models.Q(rating__lte=5.0),
                name='restaurant_rating_range'
            ),
            models.CheckConstraint(
                condition=models.Q(min_order_amount__gte=0.0),
                name='restaurant_min_order_positive'
            ),
            models.CheckConstraint(
                condition=models.Q(delivery_fee__gte=0.0),
                name='restaurant_delivery_fee_positive'
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.city})"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(str(self.name))
            unique_slug = base_slug
            counter = 1
            while Restaurant.objects.filter(slug=unique_slug).exclude(pk=self.pk).exists():
                unique_slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = unique_slug
        super().save(*args, **kwargs)


class EmployeeRole(models.TextChoices):
    OWNER = 'owner', _('Owner')
    MANAGER = 'manager', _('Manager')
    EDITOR = 'editor', _('Menu Editor')


class RestaurantEmployee(models.Model):
    """
    Модель RBAC для управління правами доступу до ресторану.
    Зв'язує ID користувача з Auth Service із конкретним рестораном та роллю.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='employees',
        verbose_name=_("Restaurant")
    )
    user_id = models.UUIDField(_("Auth Service User ID"), db_index=True)
    role = models.CharField(
        _("Role"),
        max_length=20,
        choices=EmployeeRole.choices,
        default=EmployeeRole.MANAGER
    )
    is_active = models.BooleanField(_("Is Active"), default=True, help_text="Deactivate instead of deleting")
    created_at = models.DateTimeField(_("Assigned At"), auto_now_add=True)

    objects = models.Manager()

    class Meta:
        db_table = "restaurant_employees"
        verbose_name = _("Restaurant Employee")
        verbose_name_plural = _("Restaurant Employees")

        constraints = [
            models.UniqueConstraint(
                fields=['restaurant', 'user_id'],
                name='unique_restaurant_employee'
            )
        ]

    def __str__(self):
        return f"User {self.user_id} - {self.get_role_display()} at {self.restaurant.name}"
