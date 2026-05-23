from django.db import models


class GiderKategori(models.Model):
    ad = models.CharField(max_length=80, unique=True)

    class Meta:
        ordering = ["ad"]
        verbose_name = "Gider Kategorisi"
        verbose_name_plural = "Gider Kategorileri"

    def __str__(self):
        return self.ad


class Gider(models.Model):
    ODEME = [
        ("nakit", "Nakit"),
        ("banka", "Banka"),
        ("kredi_karti", "Kredi Kartı"),
        ("cek", "Çek"),
        ("diger", "Diğer"),
    ]
    KDV_ORANLARI = [(0, "%0"), (1, "%1"), (8, "%8"), (10, "%10"), (20, "%20")]

    kategori = models.ForeignKey(
        GiderKategori, on_delete=models.SET_NULL, null=True, blank=True, related_name="giderler"
    )
    tarih = models.DateField()
    aciklama = models.CharField(max_length=255)
    kdv_haric_tutar = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    kdv_orani = models.SmallIntegerField(choices=KDV_ORANLARI, default=20)
    belge_no = models.CharField(max_length=60, blank=True, verbose_name="Belge/F atura No")
    odeme_yontemi = models.CharField(max_length=20, choices=ODEME, default="nakit")
    notlar = models.TextField(blank=True)
    olusturuldu = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-tarih"]
        verbose_name = "Gider"
        verbose_name_plural = "Giderler"

    def __str__(self):
        return f"{self.tarih} – {self.aciklama} ({self.kdv_dahil_tutar} ₺)"

    @property
    def kdv_tutari(self):
        return self.kdv_haric_tutar * self.kdv_orani / 100

    @property
    def kdv_dahil_tutar(self):
        return self.kdv_haric_tutar + self.kdv_tutari
