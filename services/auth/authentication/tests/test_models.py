import uuid
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError
from django.utils import timezone

from authentication.models import RefreshTokenBlacklist

User = get_user_model()


@pytest.mark.django_db
class TestUserModel:
    """
    Тестування моделі User та її менеджера (CustomUserManager).
    """

    def test_create_user_success(self):
        user = User.objects.create_user(
            email="test_customer@example.com",
            password="SecurePassword123!"
        )

        assert user.email == "test_customer@example.com"
        assert user.check_password("SecurePassword123!") is True
        assert user.role == "customer"
        assert user.is_active is True
        assert user.is_staff is False
        assert user.is_superuser is False
        assert str(user) == "test_customer@example.com"

    def test_create_user_without_email_raises_error(self):
        with pytest.raises(ValueError, match="Email must be set"):
            User.objects.create_user(email="", password="SecurePassword123!")

    def test_create_superuser_success(self):
        admin = User.objects.create_superuser(
            email="admin@example.com",
            password="AdminPassword123!",
            role="admin"
        )

        assert admin.email == "admin@example.com"
        assert admin.role == "admin"
        assert admin.is_active is True
        assert admin.is_staff is True
        assert admin.is_superuser is True

    def test_create_superuser_missing_is_staff(self):
        with pytest.raises(ValueError, match="Superuser must have is_staff=True."):
            User.objects.create_superuser(
                email="fake_admin@example.com",
                password="pass",
                is_staff=False
            )

    def test_create_superuser_missing_is_superuser(self):
        with pytest.raises(ValueError, match="Superuser must have is_superuser=True."):
            User.objects.create_superuser(
                email="fake_admin@example.com",
                password="pass",
                is_superuser=False
            )


@pytest.mark.django_db
class TestRefreshTokenBlacklistModel:
    """
    Тестування моделі чорного списку токенів.
    """

    def test_create_blacklisted_token_success(self):
        jti = str(uuid.uuid4())
        user_id = uuid.uuid4()
        expires = timezone.now() + timedelta(days=1)

        token = RefreshTokenBlacklist.objects.create(
            jti=jti,
            user_id=user_id,
            expires_at=expires
        )

        assert token.jti == jti
        assert token.user_id == user_id
        assert str(token) == f"Blacklisted Token {jti} (User: {user_id})"

    def test_unique_jti_constraint(self):
        jti = str(uuid.uuid4())
        user_id = uuid.uuid4()
        expires = timezone.now() + timedelta(days=1)

        RefreshTokenBlacklist.objects.create(
            jti=jti,
            user_id=user_id,
            expires_at=expires
        )

        with pytest.raises(IntegrityError):
            RefreshTokenBlacklist.objects.create(
                jti=jti,
                user_id=uuid.uuid4(),
                expires_at=expires
            )
