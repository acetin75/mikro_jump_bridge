"""
Yetki sistemi — rol bazlı erişim kontrolü.

3 rol:
  Yönetici    → tüm işlemler (silme dahil)
  Muhasebeci  → okuma + ekleme + düzenleme (silme YOK)
  Görüntüleyici → sadece okuma ve raporlar

Superuser / staff her zaman tam yetkilidir.

Kullanım (view dekoratörü):
    from muhasebe_buro.permissions import yonetici_gerekli, muhasebeci_gerekli

    @yonetici_gerekli
    def cari_sil(request, pk): ...

    @muhasebeci_gerekli
    def cari_ekle(request): ...

Middleware (settings.py'ye ekle, LoginZorunluMiddleware'den sonra):
    "muhasebe_buro.permissions.YetkiMiddleware",
    "muhasebe_buro.permissions.AktiviteMiddleware",
"""

import logging
import re
from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect

logger = logging.getLogger("muhasebe")

# URL örüntüleri ─────────────────────────────────────────────────────────────
# /123/sil/ veya /sil/ şeklinde biten yollar
_SIL_RE = re.compile(r"/sil/")

# Yazma URL'leri (/ekle/, /duzenle/, /yukle/, /eslestir/, /durum/)
_YAZMA_RE = re.compile(r"/(ekle|duzenle|yukle|eslestir|durum)/")

# Muaf URL'ler (her zaman erişilebilir)
_MUAF_RE = re.compile(r"^(/admin/|/hesap/|/__debug__/)")


# ── Yardımcı fonksiyonlar ────────────────────────────────────────────────────

def yonetici_mi(user) -> bool:
    """Kullanıcı Yönetici grubunda mı (veya superuser/staff)?"""
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True
    return user.groups.filter(name="Yönetici").exists()


def muhasebeci_mi(user) -> bool:
    """Kullanıcı Muhasebeci veya Yönetici grubunda mı?"""
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True
    return user.groups.filter(name__in=["Yönetici", "Muhasebeci"]).exists()


def rol_adi(user) -> str:
    """Kullanıcının rol adını döndür (şablon için)."""
    if not user.is_authenticated:
        return ""
    if user.is_superuser:
        return "Süper Yönetici"
    if user.is_staff:
        return "Personel"
    gruplar = list(user.groups.values_list("name", flat=True))
    return gruplar[0] if gruplar else "Görüntüleyici"


# ── Dekoratörler ─────────────────────────────────────────────────────────────

def yonetici_gerekli(view_func):
    """Sadece Yönetici grubundakiler erişebilir."""
    @wraps(view_func)
    def _wrapper(request, *args, **kwargs):
        if not yonetici_mi(request.user):
            messages.error(request, "Bu işlem için Yönetici yetkisi gereklidir.")
            logger.warning(
                "Yetkisiz silme girişimi: kullanıcı=%s yol=%s",
                request.user.username, request.path,
            )
            return redirect(request.META.get("HTTP_REFERER", "/"))
        return view_func(request, *args, **kwargs)
    return _wrapper


def muhasebeci_gerekli(view_func):
    """Muhasebeci veya Yönetici grubundakiler erişebilir."""
    @wraps(view_func)
    def _wrapper(request, *args, **kwargs):
        if not muhasebeci_mi(request.user):
            messages.error(request, "Bu işlem için en az Muhasebeci yetkisi gereklidir.")
            logger.warning(
                "Yetkisiz yazma girişimi: kullanıcı=%s yol=%s",
                request.user.username, request.path,
            )
            return redirect(request.META.get("HTTP_REFERER", "/"))
        return view_func(request, *args, **kwargs)
    return _wrapper


# ── Middleware: URL tabanlı otomatik yetki kontrolü ──────────────────────────

class YetkiMiddleware:
    """
    URL örüntüsüne göre otomatik yetki kontrolü yapar.
    - /sil/ içeren URL'ler → Yönetici gerekli
    - /ekle/, /duzenle/ vb. → Muhasebeci gerekli
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user
        path = request.path

        # Muaf URL'ler veya giriş yapmamış kullanıcı (login middleware halleder)
        if _MUAF_RE.match(path) or not user.is_authenticated:
            return self.get_response(request)

        # Superuser/staff her şeye erişebilir
        if user.is_superuser or user.is_staff:
            return self.get_response(request)

        if _SIL_RE.search(path):
            if not user.groups.filter(name="Yönetici").exists():
                messages.error(request, "Silme işlemi için Yönetici yetkisi gereklidir.")
                logger.warning(
                    "Yetkisiz URL erişimi (sil): kullanıcı=%s yol=%s",
                    user.username, path,
                )
                return redirect(request.META.get("HTTP_REFERER", "/"))

        elif _YAZMA_RE.search(path):
            if not user.groups.filter(name__in=["Yönetici", "Muhasebeci"]).exists():
                messages.error(request, "Bu işlem için en az Muhasebeci yetkisi gereklidir.")
                logger.warning(
                    "Yetkisiz URL erişimi (yazma): kullanıcı=%s yol=%s",
                    user.username, path,
                )
                return redirect(request.META.get("HTTP_REFERER", "/"))

        return self.get_response(request)


# ── Middleware: Aktivite Kaydı ────────────────────────────────────────────────

class AktiviteMiddleware:
    """
    POST isteklerini aktivite loguna kaydeder.
    Sadece başarılı (302 redirect sonucu olan) işlemleri loglar.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if (
            request.method == "POST"
            and request.user.is_authenticated
            and response.status_code == 302
            and not _MUAF_RE.match(request.path)
        ):
            try:
                from kullanici.models import AktiviteLogu
                AktiviteLogu.objects.create(
                    kullanici=request.user,
                    yol=request.path[:200],
                    ip=request.META.get("REMOTE_ADDR", "")[:45],
                )
            except Exception:
                pass  # Aktivite logu hatası uygulamayı durdurmamalı

        return response
