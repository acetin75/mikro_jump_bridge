import json
import shutil
import tempfile
from datetime import date
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.http import FileResponse, HttpResponseBadRequest
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST


def index(request):
    from cari.models import Cari, HesapHareketi
    from banka.models import BankaHareketi, BankaEkstre
    from sozlesme.models import Sozlesme
    from tahsilat.models import Tahsilat

    bugun = timezone.now().date()
    ay_baslangic = bugun.replace(day=1)
    otuz_gun_sonra = bugun + timezone.timedelta(days=30)

    # Özet kartlar
    toplam_cari = Cari.objects.filter(aktif=True).count()
    aktif_sozlesme = Sozlesme.objects.filter(durum="aktif").count()
    bekleyen_ekstre = BankaEkstre.objects.filter(islendi=False).count()
    eslesmemis_hareket = BankaHareketi.objects.filter(eslesti=False).count()

    # Bu ay tahsilat / ödeme
    bu_ay_tahsilat = (
        Tahsilat.objects.filter(tarih__gte=ay_baslangic, tip="tahsilat")
        .aggregate(Sum("tutar"))["tutar__sum"] or 0
    )
    bu_ay_odeme = (
        Tahsilat.objects.filter(tarih__gte=ay_baslangic, tip="odeme")
        .aggregate(Sum("tutar"))["tutar__sum"] or 0
    )

    # Bakiyesi eksi olan cariler (borçlu)
    son_hareketler = HesapHareketi.objects.select_related("cari").order_by("-tarih", "-pk")[:15]

    # Alacak bakiyesi yüksek 10 cari
    buyuk_alacaklilar = (
        Cari.objects.filter(aktif=True)
        .annotate(
            t_alacak=Sum("hareketler__alacak"),
            t_borc=Sum("hareketler__borc"),
        )
        .order_by("-t_alacak")[:10]
    )

    # ── BİLDİRİMLER ──────────────────────────────────────────────────────────
    try:
        from ceksenet.models import CekSenet
        vadesi_gecen_cek_sayisi = CekSenet.objects.filter(
            durum="beklemede", vade_tarihi__lt=bugun
        ).count()
        yaklasan_cek_sayisi = CekSenet.objects.filter(
            durum="beklemede",
            vade_tarihi__gte=bugun,
            vade_tarihi__lte=otuz_gun_sonra,
        ).count()
        vadesi_gecen_cekler = CekSenet.objects.filter(
            durum="beklemede", vade_tarihi__lt=bugun
        ).select_related("cari").order_by("vade_tarihi")[:5]
    except Exception:
        vadesi_gecen_cek_sayisi = 0
        yaklasan_cek_sayisi = 0
        vadesi_gecen_cekler = []

    try:
        from fatura.models import Fatura
        vadesi_gecen_fatura_sayisi = sum(
            1 for f in Fatura.objects.filter(durum__in=["kesildi"])
            if f.vadesi_gecti_mi
        )
        bu_ay_satis = sum(
            f.genel_toplam for f in Fatura.objects.filter(
                tip="satis", durum__in=["kesildi", "odendi"],
                tarih__gte=ay_baslangic,
            )
        ) or 0
        bu_ay_alis = sum(
            f.genel_toplam for f in Fatura.objects.filter(
                tip="alis", durum__in=["kesildi", "odendi"],
                tarih__gte=ay_baslangic,
            )
        ) or 0
    except Exception:
        vadesi_gecen_fatura_sayisi = 0
        bu_ay_satis = 0
        bu_ay_alis = 0

    try:
        from gider.models import Gider
        bu_ay_gider = sum(
            g.kdv_dahil_tutar for g in Gider.objects.filter(tarih__gte=ay_baslangic)
        ) or 0
    except Exception:
        bu_ay_gider = 0

    # Sözleşme bitiş uyarısı (30 gün içinde biten)
    bitis_yaklasan = Sozlesme.objects.filter(
        durum="aktif",
        bitis_tarihi__gte=bugun,
        bitis_tarihi__lte=otuz_gun_sonra,
    ).count() if hasattr(Sozlesme, "bitis_tarihi") else 0

    # Toplam bildirim sayısı (badge için)
    toplam_bildirim = (
        vadesi_gecen_cek_sayisi + vadesi_gecen_fatura_sayisi
        + eslesmemis_hareket + bekleyen_ekstre + bitis_yaklasan
    )

    # ── GRAFİK VERİSİ ────────────────────────────────────────────────────────
    # Son 6 ay aylık satış ve gider
    aylik_etiketler = []
    aylik_satis_data = []
    aylik_gider_data = []
    AY_ADLARI = ["Oca", "Şub", "Mar", "Nis", "May", "Haz",
                 "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"]

    try:
        from fatura.models import Fatura
        from gider.models import Gider

        for i in range(5, -1, -1):
            ay = bugun.month - i
            yil = bugun.year
            if ay <= 0:
                ay += 12
                yil -= 1
            ay_bas = date(yil, ay, 1)
            ay_bit = date(yil + 1, 1, 1) if ay == 12 else date(yil, ay + 1, 1)

            aylik_etiketler.append(f"{AY_ADLARI[ay - 1]} {yil}")

            satis = sum(
                f.genel_toplam for f in Fatura.objects.filter(
                    tip="satis", durum__in=["kesildi", "odendi"],
                    tarih__gte=ay_bas, tarih__lt=ay_bit,
                )
            )
            aylik_satis_data.append(float(satis or 0))

            gider = sum(
                g.kdv_dahil_tutar for g in Gider.objects.filter(
                    tarih__gte=ay_bas, tarih__lt=ay_bit,
                )
            )
            aylik_gider_data.append(float(gider or 0))
    except Exception:
        pass

    # Cari tip dağılımı
    cari_dagilim_etiketler = []
    cari_dagilim_data = []
    TIP_ETIKET = {"musteri": "Müşteri", "tedarikci": "Tedarikçi", "diger": "Diğer"}
    try:
        from cari.models import Cari as CariModel
        for item in CariModel.objects.filter(aktif=True).values("tip").annotate(sayi=Count("id")):
            cari_dagilim_etiketler.append(TIP_ETIKET.get(item["tip"], item["tip"]))
            cari_dagilim_data.append(item["sayi"])
    except Exception:
        pass

    grafik = {
        "aylik_etiketler": json.dumps(aylik_etiketler),
        "aylik_satis": json.dumps(aylik_satis_data),
        "aylik_gider": json.dumps(aylik_gider_data),
        "cari_etiketler": json.dumps(cari_dagilim_etiketler),
        "cari_data": json.dumps(cari_dagilim_data),
    }

    context = {
        "toplam_cari": toplam_cari,
        "aktif_sozlesme": aktif_sozlesme,
        "bekleyen_ekstre": bekleyen_ekstre,
        "eslesmemis_hareket": eslesmemis_hareket,
        "bu_ay_tahsilat": bu_ay_tahsilat,
        "bu_ay_odeme": bu_ay_odeme,
        "son_hareketler": son_hareketler,
        "buyuk_alacaklilar": buyuk_alacaklilar,
        # bildirimler
        "vadesi_gecen_cek_sayisi": vadesi_gecen_cek_sayisi,
        "yaklasan_cek_sayisi": yaklasan_cek_sayisi,
        "vadesi_gecen_cekler": vadesi_gecen_cekler,
        "vadesi_gecen_fatura_sayisi": vadesi_gecen_fatura_sayisi,
        "bitis_yaklasan": bitis_yaklasan,
        "toplam_bildirim": toplam_bildirim,
        # bu ay fatura/gider
        "bu_ay_satis": bu_ay_satis,
        "bu_ay_alis": bu_ay_alis,
        "bu_ay_gider": bu_ay_gider,
        "bugun": bugun,
        "grafik": grafik,
    }
    return render(request, "dashboard/index.html", context)


@login_required
def yedek_indir(request):
    db_yolu = Path(settings.BASE_DIR) / "db.sqlite3"
    if not db_yolu.exists():
        messages.error(request, "Veritabanı dosyası bulunamadı.")
        return redirect("dashboard")
    bugun = date.today().strftime("%Y%m%d")
    dosya_adi = f"muhasebe_yedek_{bugun}.sqlite3"
    return FileResponse(
        open(db_yolu, "rb"),
        as_attachment=True,
        filename=dosya_adi,
    )


@login_required
@require_POST
def yedek_yukle(request):
    from muhasebe_buro.permissions import yonetici_mi
    if not yonetici_mi(request.user):
        messages.error(request, "Yedek yüklemek için Yönetici yetkisi gereklidir.")
        return redirect("dashboard")

    dosya = request.FILES.get("yedek_dosya")
    if not dosya or not dosya.name.endswith(".sqlite3"):
        messages.error(request, "Geçerli bir .sqlite3 dosyası seçin.")
        return redirect("dashboard")

    db_yolu = Path(settings.BASE_DIR) / "db.sqlite3"
    # Önce mevcut DB'yi yedekle
    yedek_yolu = Path(settings.BASE_DIR) / f"db_onceki_yedek.sqlite3"
    shutil.copy2(db_yolu, yedek_yolu)

    # Yeni dosyayı yaz
    with open(db_yolu, "wb") as f:
        for chunk in dosya.chunks():
            f.write(chunk)

    messages.success(request, "Yedek başarıyla yüklendi. Eski veritabanı 'db_onceki_yedek.sqlite3' olarak korundu.")
    return redirect("dashboard")
