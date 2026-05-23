import logging
from decimal import Decimal
from django.db import models
from django.db.models import Sum

logger = logging.getLogger("muhasebe")


class KasaHesabi(models.Model):
    ad = models.CharField("Kasa Adı", max_length=100)
    para_birimi = models.CharField("Para Birimi", max_length=3, default="TRY")
    acilis_bakiyesi = models.DecimalField(
        "Açılış Bakiyesi", max_digits=14, decimal_places=2, default=0
    )
    aktif = models.BooleanField("Aktif", default=True)
    aciklama = models.CharField("Açıklama", max_length=200, blank=True)
    olusturuldu = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["ad"]
        verbose_name = "Kasa Hesabı"
        verbose_name_plural = "Kasa Hesapları"

    def __str__(self):
        return self.ad

    @property
    def toplam_giris(self):
        return (
            self.hareketler.filter(tip="giris").aggregate(Sum("tutar"))["tutar__sum"]
            or Decimal("0")
        )

    @property
    def toplam_cikis(self):
        return (
            self.hareketler.filter(tip="cikis").aggregate(Sum("tutar"))["tutar__sum"]
            or Decimal("0")
        )

    @property
    def mevcut_bakiye(self):
        return self.acilis_bakiyesi + self.toplam_giris - self.toplam_cikis


class KasaHareketi(models.Model):
    TIP = [
        ("giris", "Giriş (Nakit Geldi)"),
        ("cikis", "Çıkış (Nakit Gitti)"),
    ]

    kasa = models.ForeignKey(
        KasaHesabi,
        on_delete=models.PROTECT,
        related_name="hareketler",
        verbose_name="Kasa",
    )
    tarih = models.DateField("Tarih")
    tip = models.CharField("Tip", max_length=10, choices=TIP)
    tutar = models.DecimalField("Tutar", max_digits=14, decimal_places=2)
    aciklama = models.CharField("Açıklama", max_length=300, blank=True)
    belge_no = models.CharField("Belge No", max_length=50, blank=True)

    # Kaynak bağlantıları — hangisi doluysa o tetikledi; hepsi null = manuel
    tahsilat = models.OneToOneField(
        "tahsilat.Tahsilat",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="kasa_hareketi",
        verbose_name="Tahsilat",
    )
    gider = models.OneToOneField(
        "gider.Gider",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="kasa_hareketi",
        verbose_name="Gider",
    )
    fatura = models.ForeignKey(
        "fatura.Fatura",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="kasa_hareketleri",
        verbose_name="Fatura",
    )

    olusturuldu = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-tarih", "-olusturuldu"]
        verbose_name = "Kasa Hareketi"
        verbose_name_plural = "Kasa Hareketleri"

    def __str__(self):
        return f"{self.get_tip_display()} | {self.tutar} ₺ | {self.tarih}"

    @property
    def kaynak_aciklamasi(self):
        if self.tahsilat_id:
            t = self.tahsilat
            return f"Tahsilat — {t.cari}"
        if self.gider_id:
            g = self.gider
            return f"Gider — {g.aciklama}"
        if self.fatura_id:
            return f"Fatura {self.fatura.fatura_no}"
        return "Manuel"

    @property
    def otomatik_mi(self):
        return bool(self.tahsilat_id or self.gider_id or self.fatura_id)
