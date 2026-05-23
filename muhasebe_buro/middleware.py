"""
Her sayfaya giriş zorunluluğu getirir.
Muaf tutulan URL'ler: /admin/, /hesap/giris/, /hesap/cikis/
"""
from django.conf import settings
from django.shortcuts import redirect


MUAF_URL_ONEKLERI = [
    "/admin/",
    "/hesap/giris/",
    "/hesap/cikis/",
]


class LoginZorunluMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            if not any(request.path.startswith(p) for p in MUAF_URL_ONEKLERI):
                return redirect(f"{settings.LOGIN_URL}?next={request.path}")
        return self.get_response(request)
