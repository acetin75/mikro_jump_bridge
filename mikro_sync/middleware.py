"""
Her sayfaya giriş ve firma seçimi zorunluluğu getirir.
"""

from django.conf import settings
from django.shortcuts import redirect

MUAF_URL_ONEKLERI = [
    "/admin/",
    "/giris/",
    "/cikis/",
]

# Firma seçimi zorunluluğundan muaf yollar:
# - Firma yönetim sayfaları (firma ekle/düzenle — henüz firma yokken erişebilmek için)
# - Seçim sayfasının kendisi
FIRMA_SEC_MUAF_ONEKLERI = MUAF_URL_ONEKLERI + [
    "/firmalar/",
    "/hesap/firma-sec/",
    "/hesap/firma-baglanti-test/",  # AJAX endpoint — firma seçimi henüz yapılmamış olabilir
    "/static/",
    "/lisans/",  # Lisans sayfaları firma seçimi gerektirmez
    "/posta/",  # Posta ayarları firma seçimi gerektirmez
    "/kullanicilar/",  # Kullanıcı yönetimi firma seçimi gerektirmez
]


class LoginZorunluMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            if not any(request.path.startswith(p) for p in MUAF_URL_ONEKLERI):
                return redirect(f"{settings.LOGIN_URL}?next={request.path}")
        return self.get_response(request)


class FirmaSecimZorunluMiddleware:
    """
    Giriş yapmış kullanıcı, session'da aktif firma seçimi yoksa
    /hesap/firma-sec/ sayfasına yönlendirilir.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            if not any(request.path.startswith(p) for p in FIRMA_SEC_MUAF_ONEKLERI):
                if "aktif_firma_id" not in request.session:
                    return redirect(f"/hesap/firma-sec/?next={request.path}")
        return self.get_response(request)
