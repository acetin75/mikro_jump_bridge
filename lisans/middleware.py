"""
Lisans kontrolü middleware.
Deneme süresi veya lisans bitmişse /lisans/bitti/ sayfasına yönlendirir.
"""
from django.shortcuts import redirect
from django.urls import reverse

# Bu URL önekleri lisans kontrolünden muaftır
_MUAF = (
    "/lisans/",
    "/admin/",
    "/giris/",
    "/cikis/",
    "/static/",
    "/media/",
)


class LisansKontrolMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Muaf yollar ve AJAX istekleri doğrudan geçer
        if any(request.path.startswith(p) for p in _MUAF):
            return self.get_response(request)
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return self.get_response(request)

        # Giriş yapmamış kullanıcı: LoginZorunluMiddleware zaten devreye girer
        if not request.user.is_authenticated:
            return self.get_response(request)

        # Lisans geçerlilik kontrolü
        from lisans.utils import lisans_al
        lisans = lisans_al()

        if not lisans.gecerli_mi:
            return redirect(reverse("lisans_suresi_doldu"))

        return self.get_response(request)
