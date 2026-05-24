"""
Hesap Yönetimi — Mikro ERP cari hesap sorgulama ekranları.

Tüm sorgular seçili firmaya ait MikroApiClient üzerinden yapılır.
Aktif firma session'da tutulur: request.session["aktif_firma_id"]
"""
import logging
from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render

from sync_motor.client import MikroApiClient, MikroApiHatasi
from sync_motor.models import FirmaAyar

logger = logging.getLogger("mikro_sync")


def _aktif_firma(request):
    """Session'dan aktif FirmaAyar döndürür; yoksa None."""
    firma_id = request.session.get("aktif_firma_id")
    if not firma_id:
        return None
    return FirmaAyar.objects.filter(pk=firma_id, aktif=True).first()


def _aktif_client(request):
    """Session'daki firma + bağlantı modundan MikroApiClient döndürür."""
    firma = _aktif_firma(request)
    if not firma:
        return None
    mod = request.session.get("aktif_baglanti_modu", "yerel")
    sunucu_ip = firma.sunucu_al(mod)
    return MikroApiClient(firma, sunucu_ip=sunucu_ip)


# ---------------------------------------------------------------------------
# AKTİF FİRMA SEÇİMİ
# ---------------------------------------------------------------------------

@login_required
def firma_sec(request):
    """
    GET  → firma + bağlantı modu seçim ekranı
    POST → session'a yazar, yönlendirir
    """
    firmalar = FirmaAyar.objects.filter(aktif=True).order_by("ad")
    if not firmalar.exists():
        messages.warning(request, "Henüz firma eklenmemiş. Lütfen önce firma ekleyin.")
        return redirect("firma_ekle")

    if request.method == "POST":
        firma_id = request.POST.get("firma_id")
        baglanti_modu = request.POST.get("baglanti_modu", "yerel")
        firma = FirmaAyar.objects.filter(pk=firma_id, aktif=True).first()
        if firma:
            # Seçilen modun bu firmada tanımlı olduğunu doğrula
            gecerli_modlar = [m[0] for m in firma.baglanti_modlari]
            if baglanti_modu not in gecerli_modlar:
                baglanti_modu = gecerli_modlar[0] if gecerli_modlar else "yerel"
            request.session["aktif_firma_id"] = int(firma_id)
            request.session["aktif_baglanti_modu"] = baglanti_modu
            mod_adi = dict([(m[0], m[1]) for m in firma.baglanti_modlari]).get(baglanti_modu, baglanti_modu)
            messages.success(request, f"{firma.ad} — {mod_adi} bağlantısı seçildi.")
        next_url = request.POST.get("next") or "hy_panel"
        return redirect(next_url)

    return render(request, "hesap_yonetimi/firma_sec.html", {
        "firmalar": firmalar,
        "aktif_firma": _aktif_firma(request),
        "aktif_mod": request.session.get("aktif_baglanti_modu", "yerel"),
    })


@login_required
def baglanti_test_ajax(request):
    """AJAX: Seçili firma + bağlantı modu için bağlantı testi. JSON döner."""
    if request.method != "POST":
        return JsonResponse({"basarili": False, "mesaj": "Yalnızca POST"}, status=405)
    firma_id = request.POST.get("firma_id")
    baglanti_modu = request.POST.get("baglanti_modu", "yerel")
    firma = FirmaAyar.objects.filter(pk=firma_id, aktif=True).first()
    if not firma:
        return JsonResponse({"basarili": False, "mesaj": "Firma bulunamadı."})
    sunucu_ip = firma.sunucu_al(baglanti_modu)
    client = MikroApiClient(firma, sunucu_ip=sunucu_ip)
    sonuc = client.baglanti_test()
    sonuc["sunucu"] = sunucu_ip
    logger.info("Bağlantı testi: firma=%s mod=%s basarili=%s", firma.ad, baglanti_modu, sonuc["basarili"])
    return JsonResponse(sonuc)


# ---------------------------------------------------------------------------
# PANEL
# ---------------------------------------------------------------------------

@login_required
def panel(request):
    """Hesap Yönetimi ana paneli — seçili firma özet bilgileri."""
    aktif_firma = _aktif_firma(request)
    if not aktif_firma:
        messages.warning(request, "Lütfen önce bir firma seçin.")
        return redirect("hy_firma_sec")

    ozet = {}
    try:
        client = _aktif_client(request)
        saglik = client.baglanti_test()
        ozet["baglanti"] = saglik
        sorgu = """
            SELECT
                COUNT(*) as cari_adet,
                SUM(CASE WHEN cari_bakiye > 0 THEN cari_bakiye ELSE 0 END) as toplam_alacak,
                SUM(CASE WHEN cari_bakiye < 0 THEN ABS(cari_bakiye) ELSE 0 END) as toplam_borc
            FROM CARI_HESAPLAR
            WHERE cari_baglanti_tipi = 0
        """
        sonuc = client.sql_oku(sorgu)
        if sonuc:
            ozet["cari"] = sonuc[0]
    except MikroApiHatasi as e:
        logger.error("Panel özet hatası [%s]: %s", aktif_firma.ad, e)
        messages.error(request, f"API hatası: {e}")

    return render(request, "hesap_yonetimi/panel.html", {
        "aktif_firma": aktif_firma,
        "firmalar": FirmaAyar.objects.filter(aktif=True).order_by("ad"),
        "ozet": ozet,
    })


# ---------------------------------------------------------------------------
# FİRMA KARTLARI (CARİ LİSTESİ)
# ---------------------------------------------------------------------------

@login_required
def firma_kartlari(request):
    """Mikro'dan cari hesap listesini çeker ve listeler."""
    aktif_firma = _aktif_firma(request)
    if not aktif_firma:
        messages.warning(request, "Lütfen önce bir firma seçin.")
        return redirect("hy_firma_sec")

    arama = request.GET.get("q", "").strip()
    tip_filtre = request.GET.get("tip", "")
    cariler = []

    try:
        client = _aktif_client(request)
        where = "cari_baglanti_tipi = 0"
        if arama:
            temiz = arama.replace("'", "''")
            where += f" AND (cari_unvan1 LIKE '%{temiz}%' OR cari_kod LIKE '%{temiz}%' OR cari_vkn_vd LIKE '%{temiz}%')"
        if tip_filtre == "musteri":
            where += " AND cari_isk_tip = 0"
        elif tip_filtre == "tedarikci":
            where += " AND cari_isk_tip = 1"

        sorgu = f"""
            SELECT TOP 500
                cari_kod, cari_unvan1, cari_unvan2,
                cari_vkn_vd, cari_VergiDairesi,
                cari_telefon1, cari_EMail1,
                cari_bakiye, cari_isk_tip
            FROM CARI_HESAPLAR
            WHERE {where}
            ORDER BY cari_unvan1
        """
        cariler = client.sql_oku(sorgu)
        logger.info("Firma kartları çekildi [%s]: %d cari", aktif_firma.ad, len(cariler))
    except MikroApiHatasi as e:
        logger.error("Firma kartları hatası [%s]: %s", aktif_firma.ad, e)
        messages.error(request, f"Mikro API hatası: {e}")

    return render(request, "hesap_yonetimi/firma_kartlari.html", {
        "aktif_firma": aktif_firma,
        "firmalar": FirmaAyar.objects.filter(aktif=True).order_by("ad"),
        "cariler": cariler,
        "arama": arama,
        "tip_filtre": tip_filtre,
    })


# ---------------------------------------------------------------------------
# CARİ DETAY
# ---------------------------------------------------------------------------

@login_required
def cari_detay(request, cari_kod: str):
    """Belirli bir carinin detay bilgilerini gösterir."""
    aktif_firma = _aktif_firma(request)
    if not aktif_firma:
        return redirect("hy_firma_sec")

    cari = None
    bakiye_doviz = []
    try:
        client = _aktif_client(request)
        temiz_kod = cari_kod.replace("'", "''")
        cari_sorgu = f"""
            SELECT cari_kod, cari_unvan1, cari_unvan2,
                   cari_vkn_vd, cari_VergiDairesi,
                   cari_telefon1, cari_EMail1,
                   cari_adres1, cari_adres2,
                   cari_bakiye, cari_isk_tip
            FROM CARI_HESAPLAR
            WHERE cari_kod = '{temiz_kod}' AND cari_baglanti_tipi = 0
        """
        sonuc = client.sql_oku(cari_sorgu)
        if sonuc:
            cari = sonuc[0]
    except MikroApiHatasi as e:
        logger.error("Cari detay hatası [%s] %s: %s", aktif_firma.ad, cari_kod, e)
        messages.error(request, f"Mikro API hatası: {e}")

    return render(request, "hesap_yonetimi/cari_detay.html", {
        "aktif_firma": aktif_firma,
        "firmalar": FirmaAyar.objects.filter(aktif=True).order_by("ad"),
        "cari": cari,
        "cari_kod": cari_kod,
        "bakiye_doviz": bakiye_doviz,
    })


# ---------------------------------------------------------------------------
# HESAP HAREKETLERİ
# ---------------------------------------------------------------------------

@login_required
def hesap_hareketleri(request):
    """Seçili carinin hesap hareketlerini listeler."""
    aktif_firma = _aktif_firma(request)
    if not aktif_firma:
        messages.warning(request, "Lütfen önce bir firma seçin.")
        return redirect("hy_firma_sec")

    cari_kod = request.GET.get("cari_kod", "").strip()
    baslangic = request.GET.get("baslangic", (date.today() - timedelta(days=30)).strftime("%Y-%m-%d"))
    bitis = request.GET.get("bitis", date.today().strftime("%Y-%m-%d"))
    hareketler = []
    secili_cari = None

    if cari_kod:
        try:
            client = _aktif_client(request)
            temiz_kod = cari_kod.replace("'", "''")
            cari_sorgu = f"""
                SELECT cari_kod, cari_unvan1, cari_bakiye
                FROM CARI_HESAPLAR
                WHERE cari_kod = '{temiz_kod}' AND cari_baglanti_tipi = 0
            """
            cari_sonuc = client.sql_oku(cari_sorgu)
            if cari_sonuc:
                secili_cari = cari_sonuc[0]

            sorgu = f"""
                SELECT
                    che_tarih, che_evrak_tip, che_evrak_seri, che_evrak_sira,
                    che_aciklama, che_meblag, che_normal_iade,
                    che_doviz_cinsi, che_doviz_kuru, che_belge_no
                FROM CARI_HESAP_HAREKETLERI
                WHERE che_cari_kod = '{temiz_kod}'
                  AND che_tarih BETWEEN '{baslangic}' AND '{bitis}'
                ORDER BY che_tarih DESC, che_evrak_sira DESC
            """
            hareketler = client.sql_oku(sorgu)
            logger.info("Hesap hareketleri [%s] %s: %d satır", aktif_firma.ad, cari_kod, len(hareketler))
        except MikroApiHatasi as e:
            logger.error("Hesap hareketleri hatası [%s] %s: %s", aktif_firma.ad, cari_kod, e)
            messages.error(request, f"Mikro API hatası: {e}")

    return render(request, "hesap_yonetimi/hesap_hareketleri.html", {
        "aktif_firma": aktif_firma,
        "firmalar": FirmaAyar.objects.filter(aktif=True).order_by("ad"),
        "cari_kod": cari_kod,
        "baslangic": baslangic,
        "bitis": bitis,
        "hareketler": hareketler,
        "secili_cari": secili_cari,
    })


# ---------------------------------------------------------------------------
# BAKİYE RAPORU
# ---------------------------------------------------------------------------

@login_required
def bakiye_raporu(request):
    """Tüm carilerin bakiye özeti."""
    aktif_firma = _aktif_firma(request)
    if not aktif_firma:
        messages.warning(request, "Lütfen önce bir firma seçin.")
        return redirect("hy_firma_sec")

    sadece_borclular = request.GET.get("sadece_borclular") == "1"
    sadece_alacaklilar = request.GET.get("sadece_alacaklilar") == "1"
    sirala = request.GET.get("sirala", "bakiye_desc")
    bakiyeler = []

    try:
        client = _aktif_client(request)
        where = "cari_baglanti_tipi = 0 AND cari_bakiye <> 0"
        if sadece_borclular:
            where += " AND cari_bakiye < 0"
        elif sadece_alacaklilar:
            where += " AND cari_bakiye > 0"

        order_map = {
            "bakiye_desc": "cari_bakiye DESC",
            "bakiye_asc": "cari_bakiye ASC",
            "unvan": "cari_unvan1 ASC",
        }
        order_by = order_map.get(sirala, "cari_bakiye DESC")

        sorgu = f"""
            SELECT TOP 1000
                cari_kod, cari_unvan1,
                cari_vkn_vd, cari_bakiye, cari_isk_tip
            FROM CARI_HESAPLAR
            WHERE {where}
            ORDER BY {order_by}
        """
        bakiyeler = client.sql_oku(sorgu)
        logger.info("Bakiye raporu [%s]: %d satır", aktif_firma.ad, len(bakiyeler))
    except MikroApiHatasi as e:
        logger.error("Bakiye raporu hatası [%s]: %s", aktif_firma.ad, e)
        messages.error(request, f"Mikro API hatası: {e}")

    toplam_alacak = sum(
        float(r.get("cari_bakiye", 0) or 0)
        for r in bakiyeler
        if float(r.get("cari_bakiye", 0) or 0) > 0
    )
    toplam_borc = sum(
        abs(float(r.get("cari_bakiye", 0) or 0))
        for r in bakiyeler
        if float(r.get("cari_bakiye", 0) or 0) < 0
    )

    return render(request, "hesap_yonetimi/bakiye_raporu.html", {
        "aktif_firma": aktif_firma,
        "firmalar": FirmaAyar.objects.filter(aktif=True).order_by("ad"),
        "bakiyeler": bakiyeler,
        "sadece_borclular": sadece_borclular,
        "sadece_alacaklilar": sadece_alacaklilar,
        "sirala": sirala,
        "toplam_alacak": toplam_alacak,
        "toplam_borc": toplam_borc,
    })


# ---------------------------------------------------------------------------
# ÖDEME PLANLAMA / VADESİ YAKLAŞAN ÇEKLER
# ---------------------------------------------------------------------------

@login_required
def odeme_planlama(request):
    """Vadesi yaklaşan/geçen çek-senet takibi."""
    aktif_firma = _aktif_firma(request)
    if not aktif_firma:
        messages.warning(request, "Lütfen önce bir firma seçin.")
        return redirect("hy_firma_sec")

    gun = int(request.GET.get("gun", 30))
    cekler = []
    try:
        client = _aktif_client(request)
        bitis_t = (date.today() + timedelta(days=gun)).strftime("%Y-%m-%d")
        bugun_t = date.today().strftime("%Y-%m-%d")
        sorgu = f"""
            SELECT TOP 500
                csh_evrak_no, csh_cari_kodu, ch.cari_unvan1,
                csh_tarih, csh_vade_tar,
                csh_tutar, csh_doviz_cinsi,
                csh_tip, csh_durum,
                DATEDIFF(day, GETDATE(), csh_vade_tar) as kalan_gun
            FROM CEK_SENET_HAREKETLERI csh
            JOIN CARI_HESAPLAR ch ON ch.cari_kod = csh_cari_kodu
            WHERE csh_vade_tar BETWEEN '{bugun_t}' AND '{bitis_t}'
              AND csh_durum = 0
            ORDER BY csh_vade_tar ASC
        """
        cekler = client.sql_oku(sorgu)
        logger.info("Ödeme planlama [%s]: %d çek/senet", aktif_firma.ad, len(cekler))
    except MikroApiHatasi as e:
        logger.error("Ödeme planlama hatası [%s]: %s", aktif_firma.ad, e)
        messages.error(request, f"Mikro API hatası: {e}")

    return render(request, "hesap_yonetimi/odeme_planlama.html", {
        "aktif_firma": aktif_firma,
        "firmalar": FirmaAyar.objects.filter(aktif=True).order_by("ad"),
        "cekler": cekler,
        "gun": gun,
    })
