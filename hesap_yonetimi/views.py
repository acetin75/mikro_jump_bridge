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
from sync_motor.forms import FirmaAyarForm
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

    firmalar_ile_form = [(f, FirmaAyarForm(instance=f)) for f in firmalar]
    return render(request, "hesap_yonetimi/firma_sec.html", {
        "firmalar": firmalar,
        "firmalar_ile_form": firmalar_ile_form,
        "aktif_firma": _aktif_firma(request),
        "aktif_mod": request.session.get("aktif_baglanti_modu", "yerel"),
    })


@login_required
def cari_ara_api(request):
    """Cari arama JSON API — Select2 autocomplete için."""
    q = request.GET.get("q", "").strip()
    if len(q) < 2:
        return JsonResponse({"results": []})
    aktif_firma = _aktif_firma(request)
    if not aktif_firma:
        return JsonResponse({"results": []})
    temiz_q = q.replace("'", "''")
    try:
        client = _aktif_client(request)
        data = client.sql_oku(f"""
            SELECT TOP 20 cari_kod, cari_unvan1
            FROM CARI_HESAPLAR
            WHERE cari_baglanti_tipi = 0
              AND (cari_kod LIKE '%{temiz_q}%' OR cari_unvan1 LIKE '%{temiz_q}%')
            ORDER BY cari_kod
        """)
        results = [{"id": r["cari_kod"], "text": f"{r['cari_kod']} \u2014 {r['cari_unvan1']}"} for r in data]
    except MikroApiHatasi:
        results = []
    return JsonResponse({"results": results})


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
                ISNULL((SELECT SUM(CASE WHEN cha_tip = 0 THEN cha_meblag ELSE 0 END)
                        FROM CARI_HESAP_HAREKETLERI
                        WHERE cha_kod IN (SELECT cari_kod FROM CARI_HESAPLAR WHERE cari_baglanti_tipi=0)
                          AND cha_tip = 0), 0) as toplam_alacak,
                ISNULL((SELECT SUM(CASE WHEN cha_tip = 1 THEN cha_meblag ELSE 0 END)
                        FROM CARI_HESAP_HAREKETLERI
                        WHERE cha_kod IN (SELECT cari_kod FROM CARI_HESAPLAR WHERE cari_baglanti_tipi=0)
                          AND cha_tip = 1), 0) as toplam_borc
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
    grup_filtre = request.GET.get("grup", "").strip()
    cariler = []
    gruplar = []

    try:
        client = _aktif_client(request)
        where = "cari_baglanti_tipi = 0"
        if arama:
            temiz = arama.replace("'", "''")
            where += f" AND (cari_unvan1 LIKE '%{temiz}%' OR cari_kod LIKE '%{temiz}%' OR cari_VergiKimlikNo LIKE '%{temiz}%')"
        if grup_filtre:
            temiz_grup = grup_filtre.replace("'", "''")
            where += f" AND cari_grup_kodu = '{temiz_grup}'"

        # Grup kodları dropdown için
        gruplar_sonuc = client.sql_oku("""
            SELECT DISTINCT cari_grup_kodu
            FROM CARI_HESAPLAR
            WHERE cari_baglanti_tipi = 0
              AND cari_grup_kodu IS NOT NULL
              AND cari_grup_kodu <> ''
            ORDER BY cari_grup_kodu
        """)
        gruplar = [r["cari_grup_kodu"] for r in gruplar_sonuc if r.get("cari_grup_kodu")]

        sorgu = f"""
            SELECT TOP 500
                cari_kod, cari_unvan1, cari_unvan2,
                cari_VergiKimlikNo,
                cari_CepTel, cari_EMail,
                cari_grup_kodu, cari_doviz_cinsi
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
        "gruplar": gruplar,
        "arama": arama,
        "grup_filtre": grup_filtre,
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
                   cari_VergiKimlikNo, cari_vdaire_adi,
                   cari_CepTel, cari_EMail,
                   cari_sicil_no, cari_muh_kod
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
    ilk_tarih = request.GET.get("ilk_tarih", date.today().replace(month=1, day=1).strftime("%Y-%m-%d"))
    son_tarih = request.GET.get("son_tarih", date.today().strftime("%Y-%m-%d"))

    DOVIZ_MAP = {0: "TL", 1: "USD", 2: "EUR", 8: "JPY", 12: "AED", 20: "GBP"}
    hareketler = []
    bakiye_ozet = []
    firma = None

    if cari_kod:
        try:
            client = _aktif_client(request)
            temiz_kod = cari_kod.replace("'", "''")

            # Firma bilgisi
            cari_sonuc = client.sql_oku(f"""
                SELECT cari_kod, cari_unvan1, cari_grup_kodu
                FROM CARI_HESAPLAR
                WHERE cari_kod = '{temiz_kod}' AND cari_baglanti_tipi = 0
            """)
            firma = cari_sonuc[0] if cari_sonuc else None

            # Bakiye özeti — tüm zamanlar, döviz bazlı
            bakiye_ozet = client.sql_oku(f"""
                SELECT
                    cha_d_cins AS doviz,
                    SUM(CASE WHEN cha_tip = 0 THEN cha_meblag ELSE 0 END) AS borc,
                    SUM(CASE WHEN cha_tip = 1 THEN cha_meblag ELSE 0 END) AS alacak,
                    SUM(CASE WHEN cha_tip = 0 THEN cha_meblag ELSE 0 END) -
                    SUM(CASE WHEN cha_tip = 1 THEN cha_meblag ELSE 0 END) AS bakiye
                FROM CARI_HESAP_HAREKETLERI
                WHERE cha_kod = '{temiz_kod}' AND cha_iptal = 0
                GROUP BY cha_d_cins
                ORDER BY cha_d_cins
            """)
            for oz in bakiye_ozet:
                d = int(oz.get("doviz") or 0)
                oz["doviz_adi"] = DOVIZ_MAP.get(d, str(d))
                oz["borc"] = float(oz.get("borc") or 0)
                oz["alacak"] = float(oz.get("alacak") or 0)
                oz["bakiye"] = float(oz.get("bakiye") or 0)

            # Açılış bakiyesi — ilk_tarih öncesi kümülatif (running base)
            acilis = {}
            try:
                acilis_sonuc = client.sql_oku(f"""
                    SELECT
                        cha_d_cins AS doviz,
                        SUM(CASE WHEN cha_tip = 0 THEN cha_meblag ELSE -cha_meblag END) AS bakiye
                    FROM CARI_HESAP_HAREKETLERI
                    WHERE cha_kod = '{temiz_kod}'
                      AND cha_iptal = 0
                      AND cha_tarihi < '{ilk_tarih}'
                    GROUP BY cha_d_cins
                """)
                for a in acilis_sonuc:
                    d = int(a.get("doviz") or 0)
                    acilis[d] = float(a.get("bakiye") or 0)
            except MikroApiHatasi:
                pass  # Açılış alınamazsa sıfırdan başla

            # Sorumluluk Merkezi isimleri
            sm_map = {}
            try:
                sm_sonuc = client.sql_oku("""
                    SELECT som_kod, som_isim
                    FROM SORUMLULUK_MERKEZLERI
                    WHERE som_iptal = 0
                """)
                sm_map = {str(r["som_kod"]): r["som_isim"] for r in sm_sonuc if r.get("som_kod")}
            except MikroApiHatasi:
                pass  # Tablo yoksa boş bırak

            # Hareketler — tarih aralığı, ESKİDEN YENİYE (kümülatif için)
            hareketler = client.sql_oku(f"""
                SELECT TOP 2000
                    cha_tarihi AS tarih,
                    cha_tip AS ba,
                    cha_evrakno_seri + '-' + CAST(cha_evrakno_sira AS VARCHAR) AS evrak_no,
                    cha_aciklama AS aciklama,
                    cha_srmrkkodu AS sm,
                    cha_d_kur AS kur,
                    CASE WHEN cha_tip = 0 THEN cha_meblag ELSE 0 END AS borc,
                    CASE WHEN cha_tip = 1 THEN cha_meblag ELSE 0 END AS alacak,
                    cha_d_cins AS doviz,
                    cha_vade AS vade,
                    cha_cinsi AS kaynak,
                    cha_meblag_orj_doviz_icin_gecersiz_fl AS gecersiz_fl
                FROM CARI_HESAP_HAREKETLERI
                WHERE cha_kod = '{temiz_kod}'
                  AND cha_iptal = 0
                  AND cha_tarihi >= '{ilk_tarih}'
                  AND cha_tarihi <= '{son_tarih}'
                ORDER BY cha_tarihi ASC, cha_evrakno_sira ASC
            """)

            # Kümülatif bakiye — açılış bakiyesinden başla, gecersiz_fl=1 hariç
            running = dict(acilis)
            for h in hareketler:
                d = int(h.get("doviz") or 0)
                borc = float(h.get("borc") or 0)
                alacak = float(h.get("alacak") or 0)
                gecersiz = int(h.get("gecersiz_fl") or 0)
                if gecersiz == 0:
                    running[d] = running.get(d, 0) + borc - alacak
                h["bakiye"] = running.get(d, 0)
                h["doviz_adi"] = DOVIZ_MAP.get(d, str(d))
                h["sm_adi"] = sm_map.get(str(h.get("sm") or ""), str(h.get("sm") or ""))
                h["tarih"] = str(h.get("tarih") or "")[:10]
                h["vade"] = str(h.get("vade") or "")[:10]
                h["kur"] = float(h.get("kur") or 0)

            # Görüntüde YENİDEN ESKİYE sırala
            hareketler = list(reversed(hareketler))

            # Açılış bakiyesi — şablona geçirmek için liste yap (sıfır olanları çıkar)
            acilis_liste = [
                {"doviz": d, "doviz_adi": DOVIZ_MAP.get(d, str(d)), "bakiye": b}
                for d, b in acilis.items()
                if b != 0
            ]

            logger.info("Hesap hareketleri [%s] %s: %d satır", aktif_firma.ad, cari_kod, len(hareketler))
        except MikroApiHatasi as e:
            logger.error("Hesap hareketleri hatası [%s] %s: %s", aktif_firma.ad, cari_kod, e)
            messages.error(request, f"Mikro API hatası: {e}")

    return render(request, "hesap_yonetimi/hesap_hareketleri.html", {
        "aktif_firma": aktif_firma,
        "firmalar": FirmaAyar.objects.filter(aktif=True).order_by("ad"),
        "cari_kod": cari_kod,
        "ilk_tarih": ilk_tarih,
        "son_tarih": son_tarih,
        "firma": firma,
        "bakiye_ozet": bakiye_ozet,
        "acilis_liste": acilis_liste if cari_kod else [],
        "hareketler": hareketler,
        "DOVIZ_MAP": DOVIZ_MAP,
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
        bakiye_filtre = "AND ISNULL(b.cari_bakiye, 0) <> 0"
        if sadece_borclular:
            bakiye_filtre = "AND ISNULL(b.cari_bakiye, 0) > 0"
        elif sadece_alacaklilar:
            bakiye_filtre = "AND ISNULL(b.cari_bakiye, 0) < 0"

        order_map = {
            "bakiye_desc": "ISNULL(b.cari_bakiye, 0) DESC",
            "bakiye_asc": "ISNULL(b.cari_bakiye, 0) ASC",
            "unvan": "h.cari_unvan1 ASC",
        }
        order_by = order_map.get(sirala, "ISNULL(b.cari_bakiye, 0) DESC")

        sorgu = f"""
            WITH bak AS (
                SELECT cha_kod,
                       SUM(CASE WHEN cha_tip = 0 THEN cha_meblag ELSE -cha_meblag END) AS cari_bakiye
                FROM CARI_HESAP_HAREKETLERI
                GROUP BY cha_kod
            )
            SELECT TOP 1000
                h.cari_kod, h.cari_unvan1,
                h.cari_VergiKimlikNo,
                ISNULL(b.cari_bakiye, 0) AS cari_bakiye
            FROM CARI_HESAPLAR h
            LEFT JOIN bak b ON b.cha_kod = h.cari_kod
            WHERE h.cari_baglanti_tipi = 0
              {bakiye_filtre}
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
