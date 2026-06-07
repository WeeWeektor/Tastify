import time
from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse


class AdvancedRateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.limits = getattr(settings, 'RATE_LIMITS', {})
        self.global_limit = getattr(settings, 'GLOBAL_RATE_LIMIT', None)

    @staticmethod
    def _check_limit(key: str, limit_data: dict[str, int], error_message: str) -> JsonResponse | None:
        """Універсальний метод для перевірки лімітів у кеші."""
        current_data = cache.get(key, {'count': 0, 'start': time.time()})

        if time.time() - current_data['start'] > limit_data['period']:
            current_data = {'count': 1, 'start': time.time()}
        else:
            current_data['count'] += 1

        cache.set(key, current_data, limit_data['period'])

        if current_data['count'] > limit_data['rate']:
            return JsonResponse({'detail': error_message}, status=429)

        return None

    @staticmethod
    def _get_email_from_request(request) -> str:
        data = getattr(request, 'data', {})
        email = data.get('email') or request.POST.get('email') or ''
        return str(email).lower().strip()

    def _global_rate_limit(self, ip: str) -> JsonResponse | None:
        if not self.global_limit:
            return None

        key = f"ratelimit:global:{ip}"
        message = 'Global rate limit exceeded. You are making too many requests.'
        return self._check_limit(key, self.global_limit, message)

    def _only_url_rate_limit(self, request, ip: str, path: str, limit_key: str,
                             limit_data: dict) -> JsonResponse | None:
        """Перевірка специфічного ліміту для конкретного URL або патерну."""
        rate_for_email_paths = [
            '/api/v1/auth/login/',
            '/api/v1/auth/verify-email/',
        ]

        email = ''
        if path in rate_for_email_paths:
            email = self._get_email_from_request(request)

        identifier = f"{ip}:{email}" if email else ip
        key = f"ratelimit:{limit_key}:{identifier}"

        message = 'Too many requests. Please wait.'
        return self._check_limit(key, limit_data, message)

    def __call__(self, request):
        ip = request.META.get('REMOTE_ADDR', '')

        global_response = self._global_rate_limit(ip)
        if global_response:
            return global_response

        path = request.path

        limit_data = None
        limit_key = None

        if path in self.limits:
            limit_data = self.limits[path]
            limit_key = path
        else:
            for key, data in self.limits.items():
                if path.startswith(key):
                    limit_data = data
                    limit_key = key
                    break

        if limit_data and limit_key:
            url_response = self._only_url_rate_limit(request, ip, path, limit_key, limit_data)
            if url_response:
                return url_response

        return self.get_response(request)
