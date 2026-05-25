import jwt
from django.conf import settings
from django.http import JsonResponse


class JWTAuthMiddleware:
    """
    Декодує JWT локально, використовуючи секретний ключ.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        auth_header = request.headers.get('Authorization')

        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            try:
                payload = jwt.decode(
                    token,
                    settings.JWT_SECRET_KEY,
                    algorithms=['HS256']
                )

                request.user_context = {
                    'user_id': payload.get('user_id'),
                    'role': payload.get('role'),
                    'email': payload.get('email')
                }
            except jwt.ExpiredSignatureError:
                return JsonResponse({'detail': 'Token expired'}, status=401)
            except jwt.InvalidTokenError:
                return JsonResponse({'detail': 'Invalid token'}, status=401)
        else:
            request.user_context = None

        return self.get_response(request)
