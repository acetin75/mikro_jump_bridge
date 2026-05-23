"""
Mikro Sync için REST API endpoint'leri.
Token tabanlı kimlik doğrulama — DRF gerektirmez.

Endpoint'ler:
    GET  /api/v1/ping/           → Bağlantı testi
    GET  /api/v1/cari/           → Cari listesi (id, ad, vergi_no, tip)
    POST /api/v1/fatura/aktar/   → Alış faturasını kaydet
"""

import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

logger = logging.getLogger("muhasebe")

# ------------------------------------------------------------------
# Token doğrulama
# ------------------------------------------------------------------

def _token_dogrula(request) -> bool:
    """Authorization: Token <token> başlığını doğrular."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Token "):
        return False
    token = auth[6:].strip()
    return _token_basit_dogrula(token)


def _token_basit_dogrula(token: str) -> bool:
    """settings.MIKRO_SYNC_API_TOKEN ile eşleşip eşleşmediğini kontrol eder."""
    from django.conf import settings
    beklenen = getattr(settings, "MIKRO_SYNC_API_TOKEN", "")
    return beklenen and token == beklenen


def _yetkisiz():
    return JsonResponse({"hata": "Yetkisiz erişim. Geçerli API token gerekli."}, status=401)


# ------------------------------------------------------------------
# Endpoint'ler
# ------------------------------------------------------------------

@require_http_methods(["GET"])
def ping(request):
    """Bağlantı testi."""
    if not _token_dogrula(request):
        return _yetkisiz()
    return JsonResponse({"durum": "ok", "mesaj": "Muhasebe Bürosu API çalışıyor."})


@require_http_methods(["GET"])
def cari_listesi(request):
    """Tüm aktif carileri JSON olarak döndürür."""
    if not _token_dogrula(request):
        return _yetkisiz()

    from cari.models import Cari
    cariler = Cari.objects.filter(aktif=True).values("id", "ad", "vergi_no", "tip", "email", "telefon")
    return JsonResponse(list(cariler), safe=False)


@csrf_exempt
@require_http_methods(["POST"])
def fatura_aktar(request):
    """
    Mikro'dan gelen alış faturasını Muhasebe Bürosu'na kaydeder.
    Beklenen JSON:
    {
        "fat_guid": "...",
        "cari_id": 5,
        "tarih": "2026-01-15",
        "vade_tarihi": "2026-02-15",
        "fatura_no": "ABC00001",
        "aciklama": "...",
        "genel_toplam": "1000.00",
        "kdv_toplam": "180.00",
        "satirlar": [
            {"ad": "...", "miktar": 1, "birim_fiyat": "...", "kdv_orani": 20, "tutar": "..."}
        ]
    }
    """
    if not _token_dogrula(request):
        return _yetkisiz()

    try:
        veri = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"hata": "Geçersiz JSON."}, status=400)

    zorunlu = ["cari_id", "tarih", "fatura_no"]
    eksik = [k for k in zorunlu if not veri.get(k)]
    if eksik:
        return JsonResponse({"hata": f"Eksik alanlar: {', '.join(eksik)}"}, status=400)

    try:
        from cari.models import Cari
        from fatura.models import Fatura, FaturaKalemi
        from decimal import Decimal
        from django.db import transaction

        cari = Cari.objects.get(pk=veri["cari_id"])

        # Aynı fatura_no ile daha önce eklenmiş mi?
        fat_no = veri["fatura_no"].strip()
        if Fatura.objects.filter(fatura_no=fat_no, tip="alis").exists():
            mevcut = Fatura.objects.get(fatura_no=fat_no, tip="alis")
            return JsonResponse({"durum": "mevcut", "fatura_id": mevcut.pk,
                                  "mesaj": f"Bu fatura zaten mevcut (ID: {mevcut.pk})."}) 

        with transaction.atomic():
            fatura = Fatura.objects.create(
                cari=cari,
                fatura_no=fat_no,
                tip="alis",
                durum="kesildi",
                tarih=veri["tarih"],
                vade_tarihi=veri.get("vade_tarihi") or veri["tarih"],
                aciklama=veri.get("aciklama", f"Mikro'dan aktarıldı — {veri.get('fat_guid', '')}"),
                para_birimi="TRY",
                odeme_yontemi="havale",
            )

            for satir in veri.get("satirlar", []):
                FaturaKalemi.objects.create(
                    fatura=fatura,
                    aciklama=satir.get("ad", ""),
                    miktar=Decimal(str(satir.get("miktar", 1))),
                    birim_fiyat=Decimal(str(satir.get("birim_fiyat", 0))),
                    kdv_orani=int(satir.get("kdv_orani", 20)),
                )

        logger.info("Mikro Sync fatura aktarıldı: %s (ID=%d)", fat_no, fatura.pk)
        return JsonResponse({"durum": "ok", "fatura_id": fatura.pk})

    except Cari.DoesNotExist:
        return JsonResponse({"hata": f"Cari bulunamadı (id={veri['cari_id']})"}, status=404)
    except Exception as e:
        logger.error("fatura_aktar hatası: %s", e, exc_info=True)
        return JsonResponse({"hata": str(e)}, status=500)
