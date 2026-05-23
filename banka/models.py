from django.db import models


class BankaHesabi(models.Model):
    ad = models.CharField("Hesap Adı", max_length=100)
    banka_adi = models.CharField("Banka Adı", max_length=100)
    sube = models.CharField("Şube", max_length=100, blank=True)
    hesap_no = models.CharField("Hesap No / IBAN", max_length=50, blank=True)
    para_birimi = models.CharField("Para Birimi", max_length=3, default="TRY")
    aktif = models.BooleanField("Aktif", default=True)

    class Meta:
        ordering = ["ad"]
        verbose_name = "Banka Hesabı"
        verbose_name_plural = "Banka Hesapları"

    def __str__(self):
        return f"{self.ad} — {self.banka_adi}"


class BankaEkstre(models.Model):
    """Yüklenen banka ekstresi dosyası."""

    banka_hesabi = models.ForeignKey(
        BankaHesabi,
        on_delete=models.PROTECT,
        related_name="ekstreler",
        verbose_name="Banka Hesabı",
    )
    dosya = models.FileField("Dosya (Excel/PDF)", upload_to="ekstreler/")
    yukleme_tarihi = models.DateTimeField(auto_now_add=True)
    donem_baslangic = models.DateField("Dönem Başlangıç", null=True, blank=True)
    donem_bitis = models.DateField("Dönem Bitiş", null=True, blank=True)
    notlar = models.TextField("Notlar", blank=True)
    islendi = models.BooleanField("İşlendi", default=False)

    class Meta:
        ordering = ["-yukleme_tarihi"]
        verbose_name = "Banka Ekstresi"
        verbose_name_plural = "Banka Ekstreleri"

    def __str__(self):
        return f"{self.banka_hesabi} | {self.yukleme_tarihi:%d.%m.%Y}"

    @property
    def dosya_uzantisi(self):
        if self.dosya:
            return self.dosya.name.rsplit(".", 1)[-1].lower()
        return ""


class BankaHareketi(models.Model):
    """Ekstreden parse edilmiş veya elle girilen banka hareketi."""

    GIRIS = "giris"
    CIKIS = "cikis"
    TIP = [(GIRIS, "Giriş (+)"), (CIKIS, "Çıkış (-)")]

    ekstre = models.ForeignKey(
        BankaEkstre,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="hareketler",
        verbose_name="Ekstre",
    )
    banka_hesabi = models.ForeignKey(
        BankaHesabi,
        on_delete=models.PROTECT,
        related_name="hareketler",
        verbose_name="Banka Hesabı",
    )
    islem_tarihi = models.DateField("İşlem Tarihi")
    aciklama = models.CharField("Açıklama", max_length=400)
    tutar = models.DecimalField("Tutar", max_digits=14, decimal_places=2)
    tip = models.CharField("Tip", max_length=10, choices=TIP)
    referans_no = models.CharField("Referans No", max_length=100, blank=True)
    eslesti = models.BooleanField("Cari ile Eşleşti", default=False)
    cari = models.ForeignKey(
        "cari.Cari",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="banka_hareketleri",
        verbose_name="Eşleşen Cari",
    )

    class Meta:
        ordering = ["-islem_tarihi"]
        verbose_name = "Banka Hareketi"
        verbose_name_plural = "Banka Hareketleri"

    def __str__(self):
        return f"{self.islem_tarihi:%d.%m.%Y} | {self.aciklama[:50]} | {self.tutar}"
