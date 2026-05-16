from django.utils import translation
from django.conf import settings


class APILanguageMiddleware:
    """
    Detects language from:
      1. `?lang=` query parameter (e.g., ?lang=ar)
      2. `Accept-Language` header (e.g., "ar", "en")
    Falls back to settings.LANGUAGE_CODE ('en').
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        lang = request.GET.get('lang')
        if not lang:
            lang = request.headers.get('Accept-Language', '').split(',')[0].strip()[:2]

        supported = [code for code, _ in settings.LANGUAGES]
        if lang not in supported:
            lang = settings.LANGUAGE_CODE

        translation.activate(lang)
        request.LANGUAGE_CODE = lang
        response = self.get_response(request)
        translation.deactivate()
        return response