import uuid
from decimal import Decimal

from django.db import models
from django.db.models import Q, F
from django.utils.translation import gettext_lazy as _

DISPLAY_ORDER_VERBOSE_NAME = _("Display Order")
DISPLAY_IS_ACTIVE_VERBOSE_NAME = _("Is Active")


class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    restaurant = models.ForeignKey(
        'restaurants.Restaurant',
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name=_('Restaurant')
    )
    name = models.CharField(_("Product Name"), max_length=200)
    description = models.TextField(_("Description"), blank=True, default='')

    weight_grams = models.SmallIntegerField(_("Weight in grams"), null=True, blank=True)
    calories = models.SmallIntegerField(_("Calories"), null=True, blank=True)
    allergens = models.JSONField(_("Allergens"), default=list, blank=True)
    ingredients = models.JSONField(_("Ingredients"), default=list, blank=True)

    is_spicy = models.BooleanField(_("Is Spicy"), default=False)
    is_vegetarian = models.BooleanField(_("Is Vegetarian"), default=False)
    is_vegan = models.BooleanField(_("Is Vegan"), default=False)

    is_active = models.BooleanField(DISPLAY_IS_ACTIVE_VERBOSE_NAME, default=True)

    objects = models.Manager()

    class Meta:
        db_table = "products"
        verbose_name = _("Product (Base Dish)")
        verbose_name_plural = _("Products")
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['restaurant', 'name'],
                name='unique_product_name_per_restaurant'
            ),
            models.CheckConstraint(
                check=Q(weight_grams__gte=0) | Q(weight_grams__isnull=True),
                name='check_product_weight_positive'
            ),
            models.CheckConstraint(
                check=Q(calories__gte=0) | Q(calories__isnull=True),
                name='check_product_calories_positive'
            )
        ]

    def __str__(self):
        return f"{self.name} (Product)"


class MenuCategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    restaurant = models.ForeignKey(
        'restaurants.Restaurant',
        on_delete=models.CASCADE,
        related_name='categories',
        verbose_name=_('Restaurant')
    )
    name = models.CharField(_("Category Name"), max_length=100)
    order = models.SmallIntegerField(DISPLAY_ORDER_VERBOSE_NAME, default=0)
    is_active = models.BooleanField(DISPLAY_IS_ACTIVE_VERBOSE_NAME, default=True)

    objects = models.Manager()

    class Meta:
        db_table = "menu_categories"
        verbose_name = _("Menu Category")
        verbose_name_plural = _("Menu Categories")
        ordering = ['order', 'name']
        constraints = [
            models.UniqueConstraint(
                fields=['restaurant', 'name'],
                name='unique_category_name_per_restaurant'
            )
        ]
        indexes = [
            models.Index(fields=['restaurant', 'is_active']),
        ]

    def __str__(self):
        return f"{self.name}"


class MenuItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.ForeignKey(
        MenuCategory,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('Menu Category')
    )
    base_product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='menu_items',
        verbose_name=_("Base Product"),
        help_text=_("Leave blank if this is a custom Combo/Set.")
    )

    name = models.CharField(_("Item Name"), max_length=200)
    price = models.DecimalField(_("Price"), max_digits=8, decimal_places=2)
    image_url = models.URLField(_("Image URL"), null=True, blank=True)
    prep_time_minutes = models.SmallIntegerField(_("Preparation time (minutes)"), default=15)

    is_available = models.BooleanField(_("Is Available"), default=True)
    is_active = models.BooleanField(DISPLAY_IS_ACTIVE_VERBOSE_NAME, default=True)

    objects = models.Manager()

    class Meta:
        db_table = "menu_items"
        verbose_name = _("Menu Item")
        verbose_name_plural = _("Menu Items")
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['category', 'name'],
                name='unique_item_name_per_category'
            ),
            models.CheckConstraint(
                check=Q(price__gte=0),
                name='check_menu_item_price_positive'
            ),
            models.CheckConstraint(
                check=Q(prep_time_minutes__gte=0),
                name='check_prep_time_positive'
            )
        ]
        indexes = [
            models.Index(fields=['category', 'is_active', 'is_available']),
        ]

    def __str__(self):
        return f"{self.name} - {self.price}"


class ModifierGroup(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    menu_item = models.ForeignKey(
        MenuItem,
        on_delete=models.CASCADE,
        related_name='modifier_groups',
        verbose_name=_("Menu Item")
    )
    name = models.CharField(_("Group Name"), max_length=100)

    is_required = models.BooleanField(
        _("Is Required"),
        default=False,
        help_text=_("Must the user select an option from this group? (e.g., Size is required)")
    )
    min_selections = models.SmallIntegerField(_("Minimum Selections"), default=0)
    max_selections = models.SmallIntegerField(_("Maximum Selections"), default=1)

    order = models.SmallIntegerField(DISPLAY_ORDER_VERBOSE_NAME, default=0)

    objects = models.Manager()

    class Meta:
        db_table = "modifier_groups"
        verbose_name = _("Modifier Group")
        verbose_name_plural = _("Modifier Groups")
        ordering = ['order', 'name']
        constraints = [
            models.CheckConstraint(
                check=Q(min_selections__lte=F('max_selections')),
                name='check_min_lte_max_selections'
            ),
            models.CheckConstraint(
                check=Q(min_selections__gte=0),
                name='check_min_selections_positive'
            )
        ]

    def __str__(self):
        return f"{self.name} (for {self.menu_item.name})"


class ModifierOption(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ForeignKey(
        ModifierGroup,
        on_delete=models.CASCADE,
        related_name='options',
        verbose_name=_("Modifier Group")
    )

    linked_product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='modifier_options',
        verbose_name=_("Linked Product"),
        help_text=_("If this option is a specific dish, link it here to pull ingredients/allergens.")
    )

    name = models.CharField(_("Option Name"), max_length=100)

    extra_price = models.DecimalField(
        _("Extra Price"),
        max_digits=8,
        decimal_places=2,
        default=Decimal('0.00')
    )

    is_available = models.BooleanField(_("Is Available"), default=True)
    order = models.SmallIntegerField(DISPLAY_ORDER_VERBOSE_NAME, default=0)

    objects = models.Manager()

    class Meta:
        db_table = "modifier_options"
        verbose_name = _("Modifier Option")
        verbose_name_plural = _("Modifier Options")
        ordering = ['order', 'name']
        constraints = [
            models.CheckConstraint(
                check=Q(extra_price__gte=0),
                name='check_extra_price_positive'
            )
        ]

    def __str__(self):
        return f"{self.name} (+{self.extra_price})" if self.extra_price else f"{self.name} (Free)"
