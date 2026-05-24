import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from .forms import FirmaAyarForm
from .models import FirmaAyar, ImportLog

logger = logging.getLogger("mikro_sync")


@login_required
def anasayfa(request):
    firmalar = FirmaAyar.objects.filter(aktif=True)
    son_importlar = ImportLog.objects.select_related("firma_ayar").order_by("-olusturuldu")[:10]
    return render(request, "sync_motor/anasayfa.html", {
        "firmalar": firmalar,
        "son_importlar": son_importlar,
    })


@login_required
def firma_liste(request):
    firmalar = FirmaAyar.objects.all()
    return render(request, "sync_motor/firma_liste.html", {"firmalar": firmalar})


@login_required
def firma_ekle(request):
    if request.method == "POST":
        form = FirmaAyarForm(request.POST)
        if form.is_valid():
            firma = form.save(commit=False)
            sifre = form.cleaned_data.get("mikro_sifre_gir", "")
            if sifre:
                firma.sifre_kaydet(sifre)
            firma.save()
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
            f = form.save(commit=False)
            sifre = form.cleaned_data.get("mikro_sifre_gir", "")
            if sifre:
                f.sifre_kaydet(sifre)
            f.save()
            messages.success(request, "Firma güncellendi.")
            next_url = request.POST.get("next_url", "firma_liste")
            if next_url not in ("firma_liste", "hy_firma_sec"):
                next_url = "firma_liste"
            return redirect(next_url)
    else:
        form = FirmaAyarForm(instance=firma)
    return render(request, "sync_motor/firma_form.html", {"form": form, "baslik": "Firma Düzenle", "firma": firma})


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


@login_required
def import_baslat(request, firma_pk):
    """Import sürecini başlatır: tarihleri al, fatura çek, staging'e kaydet."""
    firma = get_object_or_404(FirmaAyar, pk=firma_pk)
    if request.method == "POST":
        import json
        from datetime import date

        from mikro_gelen.models import MikroFatura

        from .client import MikroApiClient, MikroApiHatasi

        bas_str = request.POST.get("baslangic_tarih", "")
        bit_str = request.POST.get("bitis_tarih", "")
        try:
            bas = date.fromisoformat(bas_str)
            bit = date.fromisoformat(bit_str)
        except ValueError:
            messages.error(request, "Geçersiz tarih formatı.")
            return redirect("import_baslat", firma_pk=firma_pk)

        log = ImportLog.objects.create(
            firma_ayar=firma,
            baslangic_tarih=bas,
            bitis_tarih=bit,
            durum="isleniyor",
            baslayan=request.user,
        )

        try:
            client = MikroApiClient(firma)
            ham_faturalar = client.gelen_faturalar(bas, bit)

            with transaction.atomic():
                log.cekilen_adet = len(ham_faturalar)
                yeni = 0
                for f in ham_faturalar:
                    guid = f.get("fat_Guid") or f.get("fat_guid", "")
                    if not guid:
                        continue
                    _, olusturuldu = MikroFatura.objects.get_or_create(
                        fat_guid=guid,
                        defaults={
                            "firma_ayar": firma,
                            "fat_evrak_seri": f.get("fat_evrak_seri", ""),
                            "fat_evrak_sira": str(f.get("fat_evrak_sira", "")),
                            "fat_tarih": f.get("fat_tarih"),
                            "fat_cari_kod": f.get("fat_cari_kod", ""),
                            "fat_cari_unvan": f.get("fat_cari_unvan", ""),
                            "fat_toplam": f.get("fat_toplam"),
                            "fat_kdv": f.get("fat_kdv"),
                            "ham_json": json.dumps(f, ensure_ascii=False),
                            "import_log": log,
                            "durum": "ham",
                        },
                    )
                    if olusturuldu:
                        yeni += 1

                log.aktarilan_adet = yeni
                log.durum = "tamamlandi"
                log.save()

            messages.success(request, f"{log.cekilen_adet} fatura çekildi, {yeni} yeni staging'e kaydedildi.")
            return redirect("import_liste")

        except Exception as e:
            log.durum = "hata"
            log.hata_detay = str(e)
            log.save()
            logger.error("Import hatası (log=%d): %s", log.pk, e, exc_info=True)
            messages.error(request, f"Import hatası: {e}")
            return redirect("import_liste")

    return render(request, "sync_motor/import_baslat.html", {"firma": firma})
