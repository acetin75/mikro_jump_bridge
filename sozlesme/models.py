from django.db import models


class Sozlesme(models.Model):
    """Müşteri veya tedarikçi ile yapılan sözleşme."""

    DURUM = [
        ("taslak", "Taslak"),
        ("aktif", "Aktif"),
        ("tamamlandi", "Tamamlandı"),
        ("iptal", "İptal"),
    ]

    cari = models.ForeignKey(
        "cari.Cari",
        on_delete=models.PROTECT,
        related_name="sozlesmeler",
        verbose_name="Cari",
    )
    baslik = models.CharField("Başlık", max_length=200)
    sozlesme_no = models.CharField("Sözleşme No", max_length=50, blank=True)
    durum = models.CharField("Durum", max_length=20, choices=DURUM, default="taslak")
    baslangic_tarihi = models.DateField("Başlangıç Tarihi", null=True, blank=True)
    bitis_tarihi = models.DateField("Bitiş Tarihi", null=True, blank=True)
    tutar = models.DecimalField(
        "Sözleşme Tutarı", max_digits=14, decimal_places=2, null=True, blank=True
    )
    para_birimi = models.CharField("Para Birimi", max_length=3, default="TRY")
    dosya = models.FileField("Sözleşme Dosyası", upload_to="sozlesmeler/", blank=True)
    notlar = models.TextField("Notlar", blank=True)
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)
    guncelleme_tarihi = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-olusturma_tarihi"]
        verbose_name = "Sözleşme"
        verbose_name_plural = "Sözleşmeler"

    def __str__(self):
        return f"{self.sozlesme_no} — {self.baslik}" if self.sozlesme_no else self.baslik
