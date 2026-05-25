import pyotp
from django.contrib.auth import get_user_model

User = get_user_model()


class TwoFactorService:
    @classmethod
    def generate_totp_secret(cls, user) -> dict:
        """
            Генерує новий секрет та URI для створення QR-коду.
        """
        secret = pyotp.random_base32()

        user.totp_secret = secret
        user.save(update_fields=['totp_secret'])

        totp = pyotp.TOTP(secret)

        provisioning_uri = totp.provisioning_uri(
            name=user.email,
            issuer_name="Tastify"
        )

        return {
            "secret": secret,
            "uri": provisioning_uri
        }

    @classmethod
    def verify_and_enable(cls, user, code: str) -> bool:
        """
            Перевіряє перший введений код і вмикає 2FA для акаунта.
        """
        if not user.totp_secret:
            return False

        totp = pyotp.TOTP(user.totp_secret)

        if totp.verify(code):
            user.is_2fa_enabled = True
            user.save(update_fields=['is_2fa_enabled'])
            return True

        return False

    @classmethod
    def verify_login_token(cls, user, code: str) -> bool:
        """
            Перевіряє код під час стандартного логіну (якщо 2FA увімкнено).
        """
        if not user.is_2fa_enabled or not user.totp_secret:
            return False

        totp = pyotp.TOTP(user.totp_secret)
        return totp.verify(code)
