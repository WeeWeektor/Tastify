from django.conf import settings
from django.utils import translation


class GlobalLanguageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        lang = request.headers.get('Accept-Language', 'en')

        lang = lang.split(',')[0].split('-')[0]

        supported_langs = [code for code, name in settings.LANGUAGES]
        if lang not in supported_langs:
            lang = settings.LANGUAGE_CODE

        translation.activate(lang)
        request.LANGUAGE_CODE = translation.get_language()

        response = self.get_response(request)

        response['Content-Language'] = lang

        response.set_cookie('django_language', lang)

        return response
