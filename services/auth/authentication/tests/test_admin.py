import pytest
from django.contrib.admin.sites import site
from django.test import RequestFactory
from django.urls import reverse

from authentication.admin import (
    RefreshTokenBlacklistAdmin,
    CustomUserCreationForm
)
# Імпортуємо твої моделі та адмін-класи
from authentication.models import User, RefreshTokenBlacklist


@pytest.mark.django_db
class TestRefreshTokenBlacklistAdmin:
    """Тестування адмінки для чорного списку токенів."""

    def test_permissions(self):
        """Перевіряємо, що додавати/змінювати токени не можна, а видаляти — можна."""
        admin_obj = RefreshTokenBlacklistAdmin(RefreshTokenBlacklist, site)
        request = RequestFactory().get('/admin/')

        assert admin_obj.has_add_permission(request) is False
        assert admin_obj.has_change_permission(request) is False
        assert admin_obj.has_delete_permission(request) is True


@pytest.mark.django_db
class TestUserAdminViews:
    """
    Тестування того, що сторінки адмінки завантажуються без помилок (200 OK).
    """

    @pytest.fixture
    def admin_client(self, client):
        """Створюємо суперюзера та авторизуємо його в тестовому клієнті."""
        User.objects.create_superuser(
            email='admin@test.com',
            password='SuperSecretPassword123!'
        )
        client.login(email='admin@test.com', password='SuperSecretPassword123!')
        return client

    @pytest.fixture
    def regular_user(self):
        """Створюємо звичайного користувача для тестів сторінки редагування."""
        return User.objects.create_user(
            email='user@test.com',
            password='UserPassword123!',
            first_name='John',
            last_name='Doe'
        )

    def test_user_changelist_view(self, admin_client):
        """Перевірка списку користувачів (list_display, list_filter)."""
        url = reverse('admin:authentication_user_changelist')
        response = admin_client.get(url)

        assert response.status_code == 200

    def test_user_change_view(self, admin_client, regular_user):
        """Перевірка сторінки редагування користувача (fieldsets, readonly_fields)."""
        url = reverse('admin:authentication_user_change', args=[regular_user.id])
        response = admin_client.get(url)

        assert response.status_code == 200
        assert b'user@test.com' in response.content

    def test_user_add_view(self, admin_client):
        """Перевірка сторінки створення користувача (add_fieldsets)."""
        url = reverse('admin:authentication_user_add')
        response = admin_client.get(url)

        assert response.status_code == 200


@pytest.mark.django_db
class TestAdminForms:
    """Тестування кастомних форм адмінки."""

    def test_custom_user_creation_form_valid(self):
        """Перевірка, що форма створення валідна з правильними даними."""
        form = CustomUserCreationForm(data={
            'email': 'new_admin@test.com',
            'role': 'admin',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        })

        assert form.is_valid() is True

    def test_custom_user_creation_form_invalid_passwords(self):
        """Перевірка, що форма не пропустить різні паролі."""
        form = CustomUserCreationForm(data={
            'email': 'bad_pass@test.com',
            'role': 'customer',
            'password1': 'StrongPass123!',
            'password2': 'DifferentPass321!',
        })

        assert form.is_valid() is False

        errors = form.errors.as_data()
        assert 'password2' in errors
        assert errors['password2'][0].code == 'password_mismatch'
