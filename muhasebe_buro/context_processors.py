from django.conf import settings
from .surum_kontrol import github_surum_kontrol


def uygulama_bilgileri(request):
    kullanici = getattr(request, "user", None)
    yonetici_mi = bool(
        kullanici
        and kullanici.is_authenticated
        and (
            kullanici.is_superuser
            or kullanici.groups.filter(name="Yönetici").exists()
        )
    )

    mevcut = getattr(settings, "APP_VERSION", "?")
    surum_bilgi = {"yeni_var": False, "surum": None, "url": None}
    if (
        getattr(settings, "SURUM_KONTROL", True)
        and kullanici
        and kullanici.is_authenticated
    ):
        try:
            surum_bilgi = github_surum_kontrol(mevcut)
        except Exception:
            pass

    return {
        "APP_VERSION": mevcut,
        "kullanici_yonetici": yonetici_mi,
        "yeni_surum_var": surum_bilgi.get("yeni_var", False),
        "yeni_surum": surum_bilgi.get("surum", ""),
        "yeni_surum_url": surum_bilgi.get("url", ""),
    }
