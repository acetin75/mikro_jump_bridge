import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import FirmaAyarForm
from .models import FirmaAyar, ImportLog

logger = logging.getLogger("mikro_sync")


@login_required
def anasayfa(request):
    firmalar = FirmaAyar.objects.filter(aktif=True)
    son_importlar = ImportLog.objects.select_related("firma_ayar").order_by("-olusturuldu")[:10]
    return render(
        request,
        "sync_motor/anasayfa.html",
        {
            "firmalar": firmalar,
            "son_importlar": son_importlar,
        },
    )


@login_required
def firma_liste(request):
    firmalar = FirmaAyar.objects.all()
    return render(request, "sync_motor/firma_liste.html", {"firmalar": firmalar})


@login_required
def firma_ekle(request):
    if request.method == "POST":
        form = FirmaAyarForm(request.POST)
        if form.is_valid():
            firma = form.save()
            messages.success(request, f"{firma.ad} eklendi.")
            return redirect("firma_liste")
    else:
        form = FirmaAyarForm()
    return render(request, "sync_motor/firma_form.html", {"form": form, "baslik": "Firma Ekle"})


@login_required
def firma_duzenle(request, pk):
    firma = get_object_or_404(FirmaAyar, pk=pk)
    if request.method == "POST":
        form = FirmaAyarForm(request.POST, instance=firma)
        if form.is_valid():
            form.save()
            messages.success(request, "Firma güncellendi.")
            next_url = request.POST.get("next_url", "firma_liste")
            if next_url not in ("firma_liste", "hy_firma_sec"):
                next_url = "firma_liste"
            return redirect(next_url)
    else:
        form = FirmaAyarForm(instance=firma)
    return render(
        request,
        "sync_motor/firma_form.html",
        {"form": form, "baslik": "Firma Düzenle", "firma": firma},
    )


@login_required
def firma_test(request, pk):
    firma = get_object_or_404(FirmaAyar, pk=pk)
    sonuc = None
    if request.method == "POST":
        from .client import MikroApiClient, MikroApiHatasi

        client = MikroApiClient(firma)
        sonuc = client.baglanti_test()
        if sonuc["basarili"]:
            messages.success(request, f"Mikro API bağlantısı başarılı: {firma.mikro_sunucu}")
        else:
            messages.error(request, f"Bağlantı hatası: {sonuc['mesaj']}")
    return render(request, "sync_motor/firma_test.html", {"firma": firma, "sonuc": sonuc})


@login_required
def import_liste(request):
    importlar = ImportLog.objects.select_related("firma_ayar", "baslayan").all()
    return render(request, "sync_motor/import_liste.html", {"importlar": importlar})
