import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .models import LisansBilgisi
from .utils import lisans_anahtari_dogrula

logger = logging.getLogger("mikro_sync")


def _lisans_al() -> LisansBilgisi:
    lisans = LisansBilgisi.objects.first()
    if lisans is None:
        lisans = LisansBilgisi.objects.create()
    return lisans


@login_required
def lisans_durum(request):
    """Lisans durum sayfası — aktif lisans girişi."""
    lisans = _lisans_al()

    if request.method == "POST":
        anahtar = request.POST.get("lisans_anahtari", "").strip()
        sonuc = lisans_anahtari_dogrula(anahtar)
        if sonuc:
            lisans.lisans_tipi     = sonuc["tip"]
            lisans.lisans_anahtari = anahtar
            lisans.musteri_kodu    = sonuc["musteri"]
            lisans.lisans_bitis    = sonuc["bitis"]
            lisans.save()
            logger.info("Lisans aktifleştirildi: %s / %s", sonuc["musteri"], sonuc["bitis"])
            messages.success(
                request,
                f"✅ Lisans aktifleştirildi! "
                f"Müşteri: {sonuc['musteri']} — Bitiş: {sonuc['bitis']}",
            )
            return redirect("lisans_durum")
        else:
            messages.error(request, "Geçersiz veya süresi dolmuş lisans anahtarı.")

    return render(request, "lisans/durum.html", {"lisans": lisans})


def lisans_suresi_doldu(request):
    """Lisans süresi dolduğunda gösterilir. Anahtar girişine izin verir."""
    lisans = _lisans_al()

    if lisans.gecerli_mi:
        return redirect("hy_panel")

    if request.method == "POST":
        anahtar = request.POST.get("lisans_anahtari", "").strip()
        sonuc = lisans_anahtari_dogrula(anahtar)
        if sonuc:
            lisans.lisans_tipi     = sonuc["tip"]
            lisans.lisans_anahtari = anahtar
            lisans.musteri_kodu    = sonuc["musteri"]
            lisans.lisans_bitis    = sonuc["bitis"]
            lisans.save()
            logger.info("Süresi dolmuş lisans yenilendi: %s / %s", sonuc["musteri"], sonuc["bitis"])
            messages.success(request, "✅ Lisans başarıyla yenilendi!")
            return redirect("hy_panel")
        else:
            messages.error(request, "Geçersiz veya süresi dolmuş lisans anahtarı.")

    return render(request, "lisans/suresi_doldu.html", {"lisans": lisans})
