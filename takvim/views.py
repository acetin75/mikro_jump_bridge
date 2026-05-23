import logging
from datetime import date

from django.shortcuts import render
from django.utils import timezone

logger = logging.getLogger("muhasebe")

# Türkiye vergi takvimi — sabit yıllık takvim (ay, gün, açıklama, tip)
# tip: kdv | muhtasar | gecici | kurumlar | diger
VERGI_TAKVIMI = [
    # Ocak
    (1, 24, "Aralık KDV Beyannamesi", "kdv"),
    (1, 26, "Aralık Muhtasar Beyannamesi", "muhtasar"),
    # Şubat
    (2, 24, "Ocak KDV Beyannamesi", "kdv"),
    (2, 26, "Ocak Muhtasar Beyannamesi", "muhtasar"),
    # Mart
    (3, 24, "Şubat KDV Beyannamesi", "kdv"),
    (3, 26, "Şubat Muhtasar Beyannamesi", "muhtasar"),
    (3, 31, "Yıllık Gelir Vergisi Beyannamesi", "diger"),
    (3, 31, "Yıllık Kurumlar Vergisi Beyannamesi (önceki yıl)", "kurumlar"),
    # Nisan
    (4, 24, "Mart KDV Beyannamesi", "kdv"),
    (4, 26, "Mart Muhtasar Beyannamesi", "muhtasar"),
    (4, 30, "1. Geçici Vergi Beyannamesi (Q1)", "gecici"),
    # Mayıs
    (5, 26, "Nisan KDV Beyannamesi", "kdv"),
    (5, 26, "Nisan Muhtasar Beyannamesi", "muhtasar"),
    # Haziran
    (6, 24, "Mayıs KDV Beyannamesi", "kdv"),
    (6, 26, "Mayıs Muhtasar Beyannamesi", "muhtasar"),
    # Temmuz
    (7, 24, "Haziran KDV Beyannamesi", "kdv"),
    (7, 26, "Haziran Muhtasar Beyannamesi", "muhtasar"),
    (7, 31, "2. Geçici Vergi Beyannamesi (Q2)", "gecici"),
    # Ağustos
    (8, 26, "Temmuz KDV Beyannamesi", "kdv"),
    (8, 26, "Temmuz Muhtasar Beyannamesi", "muhtasar"),
    # Eylül
    (9, 24, "Ağustos KDV Beyannamesi", "kdv"),
    (9, 26, "Ağustos Muhtasar Beyannamesi", "muhtasar"),
    # Ekim
    (10, 24, "Eylül KDV Beyannamesi", "kdv"),
    (10, 26, "Eylül Muhtasar Beyannamesi", "muhtasar"),
    (10, 31, "3. Geçici Vergi Beyannamesi (Q3)", "gecici"),
    # Kasım
    (11, 24, "Ekim KDV Beyannamesi", "kdv"),
    (11, 26, "Ekim Muhtasar Beyannamesi", "muhtasar"),
    # Aralık
    (12, 24, "Kasım KDV Beyannamesi", "kdv"),
    (12, 26, "Kasım Muhtasar Beyannamesi", "muhtasar"),
    (12, 31, "4. Geçici Vergi Beyannamesi (Q4)", "gecici"),
]

TIP_BADGE = {
    "kdv": ("bg-primary", "KDV"),
    "muhtasar": ("bg-success", "Muhtasar"),
    "gecici": ("bg-warning text-dark", "Geçici"),
    "kurumlar": ("bg-danger", "Kurumlar"),
    "diger": ("bg-secondary", "Diğer"),
}

AY_ADLARI = [
    "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
    "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık",
]


def takvim(request):
    bugun = timezone.now().date()
    yil = int(request.GET.get("yil", bugun.year))

    # Tüm takvim olaylarını bu yıl için oluştur
    olaylar = []
    for ay, gun, aciklama, tip in VERGI_TAKVIMI:
        try:
            tarih = date(yil, ay, gun)
        except ValueError:
            continue
        gecti = tarih < bugun
        yaklasiyor = not gecti and (tarih - bugun).days <= 30
        olaylar.append({
            "tarih": tarih,
            "aciklama": aciklama,
            "tip": tip,
            "badge_class": TIP_BADGE.get(tip, ("bg-secondary", ""))[0],
            "badge_etiket": TIP_BADGE.get(tip, ("bg-secondary", tip))[1],
            "gecti": gecti,
            "yaklasiyor": yaklasiyor,
        })

    olaylar.sort(key=lambda x: x["tarih"])

    # Yaklaşan (30 gün içindeki) olaylar — dashboard widget için de kullanılabilir
    yaklasiyor_sayisi = sum(1 for o in olaylar if o["yaklasiyor"])

    return render(request, "takvim/takvim.html", {
        "olaylar": olaylar,
        "yil": yil,
        "onceki_yil": yil - 1,
        "sonraki_yil": yil + 1,
        "bugun": bugun,
        "ay_adlari": AY_ADLARI,
        "yaklasiyor_sayisi": yaklasiyor_sayisi,
    })
