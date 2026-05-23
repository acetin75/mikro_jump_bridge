from django.db import models


class Tahsilat(models.Model):
    """Müşteriden yapılan tahsilat veya tedarikçiye yapılan ödeme kaydı."""

    TIP = [
        ("tahsilat", "Tahsilat (Gelen)"),
        ("odeme", "Ödeme (Giden)"),
    ]

    YONTEM = [
        ("nakit", "Nakit"),
        ("havale", "Havale / EFT"),
        ("kredi_karti", "Kredi Kartı"),
        ("cek", "Çek"),
        ("senet", "Senet"),
        ("diger", "Diğer"),
    ]

    cari = models.ForeignKey(
        "cari.Cari",
        on_delete=models.PROTECT,
        related_name="tahsilatlar",
        verbose_name="Cari",
    )
    tip = models.CharField("Tip", max_length=15, choices=TIP, default="tahsilat")
    tarih = models.DateField("Tarih")
    tutar = models.DecimalField("Tutar", max_digits=14, decimal_places=2)
    para_birimi = models.CharField("Para Birimi", max_length=3, default="TRY")
    odeme_yontemi = models.CharField(
        "Ödeme Yöntemi", max_length=20, choices=YONTEM, default="havale"
    )
    aciklama = models.CharField("Açıklama", max_length=300, blank=True)
    belge_no = models.CharField("Makbuz / Belge No", max_length=50, blank=True)
    banka_hareketi = models.OneToOneField(
        "banka.BankaHareketi",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tahsilat",
        verbose_name="Banka Hareketi",
    )
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-tarih", "-olusturma_tarihi"]
        verbose_name = "Tahsilat / Ödeme"
        verbose_name_plural = "Tahsilatlar / Ödemeler"

    def __str__(self):
        return f"{self.get_tip_display()} | {self.cari} | {self.tutar} {self.para_birimi}"
