from django.utils import translation


class GlobalLanguageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        lang = request.headers.get('Accept-Language', 'en')
        if lang not in ['uk', 'en']:
            lang = 'en'

        translation.activate(lang)
        request.LANGUAGE_CODE = translation.get_language()

        response = self.get_response(request)
        response['Content-Language'] = lang
        return response
