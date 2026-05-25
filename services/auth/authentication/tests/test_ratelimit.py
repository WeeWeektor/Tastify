from unittest.mock import patch

import pytest
from django.core.cache import cache
from django.http import HttpResponse
from django.test import RequestFactory

from shared import AdvancedRateLimitMiddleware


def dummy_get_response(request):
    return HttpResponse(status=200)


@pytest.mark.django_db
class TestAdvancedRateLimitMiddleware:

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self, settings):
        """Ініціалізація перед кожним тестом та очищення кешу."""
        self.factory = RequestFactory()
        self.middleware = AdvancedRateLimitMiddleware(dummy_get_response)

        settings.GLOBAL_RATE_LIMIT = {'rate': 10, 'period': 60}
        settings.RATE_LIMITS = {
            '/api/v1/auth/login/': {'rate': 5, 'period': 60},
            '/api/v1/auth/register/': {'rate': 3, 'period': 3600},
        }
        self.middleware.global_limit = settings.GLOBAL_RATE_LIMIT
        self.middleware.limits = settings.RATE_LIMITS

        cache.clear()
        yield
        cache.clear()

    def test_global_rate_limit_exceeded(self):
        """Перевірка, що глобальний ліміт блокує запити на будь-які адреси."""
        for _ in range(10):
            request = self.factory.get('/api/v1/auth/some-random-path/')
            request.META['REMOTE_ADDR'] = '192.168.1.1'
            response = self.middleware(request)
            assert response.status_code == 200

        request = self.factory.get('/api/v1/auth/another-path/')
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        response = self.middleware(request)

        assert response.status_code == 429
        import json
        assert json.loads(response.content)['detail'] == 'Global rate limit exceeded. You are making too many requests.'

    def test_specific_url_limit_register(self):
        """Перевірка ліміту для /register/ (без прив'язки до email)."""
        for _ in range(3):
            request = self.factory.post('/api/v1/auth/register/')
            request.META['REMOTE_ADDR'] = '10.0.0.1'
            response = self.middleware(request)
            assert response.status_code == 200

        request = self.factory.post('/api/v1/auth/register/')
        request.META['REMOTE_ADDR'] = '10.0.0.1'
        response = self.middleware(request)

        assert response.status_code == 429
        import json
        assert json.loads(response.content)['detail'] == 'Too many requests. Please wait.'

    def test_login_limit_with_email(self):
        """Перевірка, що ліміт логіну працює правильно з email у payload."""
        email = 'target@example.com'

        for _ in range(5):
            request = self.factory.post('/api/v1/auth/login/', {'email': email})
            request.data = {'email': email}
            request.META['REMOTE_ADDR'] = '127.0.0.1'
            response = self.middleware(request)
            assert response.status_code == 200

        request = self.factory.post('/api/v1/auth/login/', {'email': email})
        request.data = {'email': email}
        request.META['REMOTE_ADDR'] = '127.0.0.1'
        response = self.middleware(request)
        assert response.status_code == 429

    def test_login_isolation_by_email(self):
        """Якщо заблоковано один email, з цього ж IP можна спробувати інший."""
        for _ in range(6):
            request = self.factory.post('/api/v1/auth/login/', {'email': 'user1@test.com'})
            request.data = {'email': 'user1@test.com'}
            request.META['REMOTE_ADDR'] = '192.168.0.5'
            response = self.middleware(request)

        assert response.status_code == 429

        request = self.factory.post('/api/v1/auth/login/', {'email': 'user2@test.com'})
        request.data = {'email': 'user2@test.com'}
        request.META['REMOTE_ADDR'] = '192.168.0.5'
        response = self.middleware(request)

        assert response.status_code == 200

    def test_email_normalization(self):
        """Перевірка, що пробіли та великі літери в email не допомагають обійти ліміт."""
        base_email = "test@domain.com"
        variations = [
            "TEST@domain.com",
            " test@domain.com",
            "test@domain.com  ",
            "TeSt@DoMaIn.CoM"
        ]

        for var in variations + [base_email]:
            request = self.factory.post('/api/v1/auth/login/', {'email': var})
            request.data = {'email': var}
            request.META['REMOTE_ADDR'] = '10.10.10.10'
            response = self.middleware(request)

            assert response.status_code == 200, f"Запит з email '{var}' неочікувано заблоковано"

        request = self.factory.post('/api/v1/auth/login/', {'email': base_email})
        request.data = {'email': base_email}
        request.META['REMOTE_ADDR'] = '10.10.10.10'
        response = self.middleware(request)

        assert response.status_code == 429

    def test_unprotected_url_bypass(self):
        """Переконатись, що URL, якого немає в RATE_LIMITS, лімітується тільки глобально."""
        for _ in range(8):
            request = self.factory.get('/api/v1/auth/safe-endpoint/')
            request.META['REMOTE_ADDR'] = '172.16.0.1'
            response = self.middleware(request)
            assert response.status_code == 200

    def test_isolation_between_different_ips(self):
        """Якщо IP-1 вичерпав ліміт, IP-2 має працювати нормально."""
        for _ in range(4):
            req_ip1 = self.factory.post('/api/v1/auth/register/')
            req_ip1.META['REMOTE_ADDR'] = '1.1.1.1'
            res_ip1 = self.middleware(req_ip1)

        assert res_ip1.status_code == 429

        req_ip2 = self.factory.post('/api/v1/auth/register/')
        req_ip2.META['REMOTE_ADDR'] = '2.2.2.2'
        res_ip2 = self.middleware(req_ip2)

        assert res_ip2.status_code == 200

    @patch('time.time')
    def test_rate_limit_resets_after_period(self, mock_time):
        """Перевірка, що ліміт знімається після завершення 'period'."""
        start_time = 1600000000.0
        mock_time.return_value = start_time

        for _ in range(5):
            req = self.factory.post('/api/v1/auth/login/', {'email': 'time@test.com'})
            req.data = {'email': 'time@test.com'}
            req.META['REMOTE_ADDR'] = '10.0.0.2'
            self.middleware(req)

        req = self.factory.post('/api/v1/auth/login/', {'email': 'time@test.com'})
        req.data = {'email': 'time@test.com'}
        req.META['REMOTE_ADDR'] = '10.0.0.2'
        assert self.middleware(req).status_code == 429

        mock_time.return_value = start_time + 61.0

        response = self.middleware(req)
        assert response.status_code == 200
