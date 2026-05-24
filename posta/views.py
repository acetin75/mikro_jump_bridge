import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from sync_motor.client import MikroApiClient, MikroApiHatasi
from sync_motor.models import FirmaAyar

from .forms import EkstreGonderForm, MailAyarForm
from .models import EkstreGonderimLog, MailAyar
from .utils import ekstre_gonder, test_maili_gonder

logger = logging.getLogger("mikro_sync")

DOVIZ_MAP = {0: "TL", 1: "USD", 2: "EUR", 8: "JPY", 12: "AED", 20: "GBP"}


def _aktif_firma(request):
    firma_id = request.session.get("aktif_firma_id")
    if not firma_id:
        return None
    try:
        return FirmaAyar.objects.get(pk=firma_id, aktif=True)
    except FirmaAyar.DoesNotExist:
        return None


# ---------------------------------------------------------------------------
# SMTP AYARLARI
# ---------------------------------------------------------------------------


@login_required
def posta_ayarlar(request):
    """SMTP gönderici ayarlarını göster ve kaydet."""
    ayar = MailAyar.objects.first()

    if request.method == "POST":
        form = MailAyarForm(request.POST, instance=ayar)
        if form.is_valid():
            obj = form.save(commit=False)
            sifre = form.cleaned_data.get("sifre", "").strip()
            if sifre:
                obj.sifre_kaydet(sifre)
            elif ayar is None:
                form.add_error("sifre", "İlk kayıt için şifre zorunludur.")
                return render(request, "posta/ayarlar.html", {"form": form, "ayar": ayar})
            obj.save()
            messages.success(request, "Mail ayarları kaydedildi.")
            return redirect("posta_ayarlar")
    else:
        form = MailAyarForm(instance=ayar)

    return render(request, "posta/ayarlar.html", {"form": form, "ayar": ayar})


@login_required
def posta_test(request):
    """SMTP bağlantısını doğrulamak için test maili gönder (POST)."""
    if request.method != "POST":
        return redirect("posta_ayarlar")

    alici = request.POST.get("test_email", "").strip()
    if not alici:
        messages.error(request, "Test için alıcı e-posta adresi girilmedi.")
        return redirect("posta_ayarlar")

    ayar = MailAyar.objects.filter(aktif=True).first()
    if not ayar:
        messages.error(request, "Önce SMTP ayarlarını kaydedin.")
        return redirect("posta_ayarlar")

    try:
        test_maili_gonder(ayar, alici)
        messages.success(request, f"Test maili gönderildi → {alici}")
    except Exception as e:
        messages.error(request, f"Gönderim hatası: {e}")
        logger.error("Test maili hatası: %s", e, exc_info=True)

    return redirect("posta_ayarlar")


# ---------------------------------------------------------------------------
# GÖNDERİM GEÇMİŞİ
# ---------------------------------------------------------------------------


@login_required
def posta_gecmis(request):
    """Ekstre gönderim geçmişi."""
    firma_filtre = request.GET.get("firma", "")
    loglar = EkstreGonderimLog.objects.select_related("firma_ayar").order_by("-olusturuldu")
    if firma_filtre:
        loglar = loglar.filter(firma_ayar_id=firma_filtre)
    firmalar = FirmaAyar.objects.filter(aktif=True).order_by("ad")
    return render(
        request,
        "posta/gonderim_gecmisi.html",
        {
            "loglar": loglar[:200],
            "firmalar": firmalar,
            "firma_filtre": firma_filtre,
        },
    )


# ---------------------------------------------------------------------------
# MANUEl EKSTRE GÖNDER (cari_detay modalından POST)
# ---------------------------------------------------------------------------


@login_required
def cari_ekstre_gonder(request):
    """Cari detay modalından ekstre gönderir."""
    if request.method != "POST":
        return redirect("hy_panel")

    aktif_firma = _aktif_firma(request)
    if not aktif_firma:
        messages.warning(request, "Lütfen önce bir firma seçin.")
        return redirect("hy_firma_sec")

    form = EkstreGonderForm(request.POST)
    cari_kod = request.POST.get("cari_kod", "").strip()

    if not form.is_valid():
        for field_errors in form.errors.values():
            for err in field_errors:
                messages.error(request, err)
        return redirect(f"/hesap/firma-kartlari/{cari_kod}/")

    cari_kod = form.cleaned_data["cari_kod"]
    cari_unvan = form.cleaned_data.get("cari_unvan", "")
    alici_email = form.cleaned_data["alici_email"]
    donem_baslangic = form.cleaned_data["donem_baslangic"]
    donem_bitis = form.cleaned_data["donem_bitis"]
    konu = form.cleaned_data.get("konu", "")

    # Mikro ERP'den hareketleri çek (yalnızca TL = doviz 0)
    hareketler = []
    acilis_bakiye = 0.0

    try:
        client = MikroApiClient(aktif_firma)
        temiz_kod = cari_kod.replace("'", "''")

        acilis_sonuc = client.sql_oku(f"""
            SELECT
                SUM(CASE WHEN cha_tip = 0 THEN cha_meblag ELSE -cha_meblag END) AS bakiye
            FROM CARI_HESAP_HAREKETLERI
            WHERE cha_kod = '{temiz_kod}'
              AND cha_iptal = 0
              AND cha_d_cins = 0
              AND cha_tarihi < '{donem_baslangic}'
        """)
        if acilis_sonuc and acilis_sonuc[0].get("bakiye") is not None:
            acilis_bakiye = float(acilis_sonuc[0]["bakiye"] or 0)

        ham = client.sql_oku(f"""
            SELECT TOP 2000
                cha_tarihi  AS tarih,
                cha_tip     AS ba,
                cha_evrakno_seri + '-' + CAST(cha_evrakno_sira AS VARCHAR) AS evrak_no,
                cha_aciklama AS aciklama,
                CASE WHEN cha_tip = 0 THEN cha_meblag ELSE 0 END AS borc,
                CASE WHEN cha_tip = 1 THEN cha_meblag ELSE 0 END AS alacak
            FROM CARI_HESAP_HAREKETLERI
            WHERE cha_kod = '{temiz_kod}'
              AND cha_iptal = 0
              AND cha_d_cins = 0
              AND cha_tarihi >= '{donem_baslangic}'
              AND cha_tarihi <= '{donem_bitis}'
            ORDER BY cha_tarihi ASC, cha_evrakno_sira ASC
        """)

        running = acilis_bakiye
        for h in ham:
            borc = float(h.get("borc") or 0)
            alacak = float(h.get("alacak") or 0)
            running += borc - alacak
            hareketler.append(
                {
                    "tarih": str(h.get("tarih") or "")[:10],
                    "evrak_no": str(h.get("evrak_no") or ""),
                    "aciklama": str(h.get("aciklama") or ""),
                    "borc": borc,
                    "alacak": alacak,
                    "bakiye": running,
                }
            )

    except MikroApiHatasi as e:
        messages.error(request, f"Mikro API hatası: {e}")
        return redirect(f"/hesap/firma-kartlari/{cari_kod}/")

    try:
        ekstre_gonder(
            firma_ayar=aktif_firma,
            cari_kod=cari_kod,
            cari_unvan=cari_unvan,
            alici_email=alici_email,
            donem_baslangic=donem_baslangic,
            donem_bitis=donem_bitis,
            hareketler=hareketler,
            acilis_bakiye=acilis_bakiye,
            konu=konu,
        )
        messages.success(request, f"Ekstre gönderildi → {alici_email}")
    except Exception as e:
        messages.error(request, f"Gönderim hatası: {e}")

    return redirect(f"/hesap/firma-kartlari/{cari_kod}/")
