"""
Kasa otomatik hareket oluşturma yardımcıları.

Kurallar:
  - Tek aktif kasa varsa → otomatik kullan
  - Birden fazla varsa → ilk aktif kasayı kullan (kullanıcı sonradan düzenleyebilir)
  - Hiç aktif kasa yoksa → sessizce atla, kullanıcıya uyarı yok
"""
import logging
from .models import KasaHesabi, KasaHareketi

logger = logging.getLogger("muhasebe")


def _aktif_kasa():
    """İlk aktif kasayı döndür; yoksa None."""
    return KasaHesabi.objects.filter(aktif=True).first()


def tahsilat_kasa_hareketi_olustur(tahsilat):
    """
    Nakit tahsilat/ödeme kaydı için otomatik kasa hareketi oluşturur.
    Zaten bir kasa hareketi varsa tekrar oluşturmaz.
    """
    if tahsilat.odeme_yontemi != "nakit":
        return
    if hasattr(tahsilat, "kasa_hareketi"):
        return  # zaten oluşturulmuş
    kasa = _aktif_kasa()
    if not kasa:
        logger.warning("Nakit tahsilat için aktif kasa bulunamadı (tahsilat pk=%s)", tahsilat.pk)
        return
    # tahsilat=gelen para → kasa girişi; odeme=giden para → kasa çıkışı
    tip = "giris" if tahsilat.tip == "tahsilat" else "cikis"
    KasaHareketi.objects.create(
        kasa=kasa,
        tarih=tahsilat.tarih,
        tip=tip,
        tutar=tahsilat.tutar,
        aciklama=tahsilat.aciklama or tahsilat.get_tip_display(),
        belge_no=tahsilat.belge_no,
        tahsilat=tahsilat,
    )
    logger.info("Kasa hareketi oluşturuldu (tahsilat pk=%s, tip=%s)", tahsilat.pk, tip)


def gider_kasa_hareketi_olustur(gider):
    """
    Nakit gider için otomatik kasa çıkış hareketi oluşturur.
    Zaten bir kasa hareketi varsa tekrar oluşturmaz.
    """
    if gider.odeme_yontemi != "nakit":
        return
    if hasattr(gider, "kasa_hareketi"):
        return
    kasa = _aktif_kasa()
    if not kasa:
        logger.warning("Nakit gider için aktif kasa bulunamadı (gider pk=%s)", gider.pk)
        return
    KasaHareketi.objects.create(
        kasa=kasa,
        tarih=gider.tarih,
        tip="cikis",
        tutar=gider.kdv_dahil_tutar,
        aciklama=gider.aciklama,
        belge_no=gider.belge_no,
        gider=gider,
    )
    logger.info("Kasa hareketi oluşturuldu (gider pk=%s)", gider.pk)


def fatura_kasa_hareketi_olustur(fatura):
    """
    Nakit ödeme yöntemiyle 'ödendi' durumuna geçen fatura için kasa hareketi.
    Fatura modelinde odeme_yontemi alanı varsa ve nakit ise çalışır.
    """
    odeme_yontemi = getattr(fatura, "odeme_yontemi", None)
    if odeme_yontemi != "nakit":
        return
    if fatura.durum != "odendi":
        return
    # Daha önce bu faturadan kasa hareketi oluşturulmuş mu?
    if KasaHareketi.objects.filter(fatura=fatura).exists():
        return
    kasa = _aktif_kasa()
    if not kasa:
        return
    # Satış faturası → kasa girişi; alış faturası → kasa çıkışı
    tip = "giris" if fatura.tip == "satis" else "cikis"
    KasaHareketi.objects.create(
        kasa=kasa,
        tarih=fatura.tarih,
        tip=tip,
        tutar=fatura.genel_toplam,
        aciklama=f"{fatura.get_tip_display()} — {fatura.fatura_no}",
        belge_no=fatura.fatura_no,
        fatura=fatura,
    )
    logger.info("Kasa hareketi oluşturuldu (fatura pk=%s, tip=%s)", fatura.pk, tip)
