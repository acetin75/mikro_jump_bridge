from django.db import models
from django.db.models import Sum


KDV_ORANLARI = [(0, "%0"), (1, "%1"), (10, "%10"), (20, "%20")]

DEGERLEME_YONTEMLERI = [
    ("ortalama", "Ağırlıklı Ortalama (WAC)"),
    ("fifo",    "FIFO — İlk Giren İlk Çıkar"),
]


class Urun(models.Model):
    kod = models.CharField("Ürün Kodu", max_length=30, unique=True, blank=True)
    ad = models.CharField("Ürün Adı", max_length=200)
    birim = models.CharField("Birim", max_length=20, default="Adet")
    kdv_orani = models.IntegerField("KDV Oranı (%)", choices=KDV_ORANLARI, default=20)
    satis_fiyati = models.DecimalField("Satış Fiyatı", max_digits=14, decimal_places=2, default=0)
    alis_fiyati = models.DecimalField("Alış Fiyatı", max_digits=14, decimal_places=2, default=0)
    min_stok = models.DecimalField("Min. Stok", max_digits=10, decimal_places=3, default=0)
    degerleme_yontemi = models.CharField(
        "Değerleme Yöntemi",
        max_length=10,
        choices=DEGERLEME_YONTEMLERI,
        default="ortalama",
        help_text="VUK Md.274 — Ağırlıklı Ortalama veya FIFO",
    )
    aktif = models.BooleanField("Aktif", default=True)
    aciklama = models.TextField("Açıklama", blank=True)
    olusturuldu = models.DateTimeField(auto_now_add=True)
    guncellendi = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["ad"]
        verbose_name = "Ürün"
        verbose_name_plural = "Ürünler"

    def __str__(self):
        return f"{self.kod} — {self.ad}" if self.kod else self.ad

    @property
    def mevcut_stok(self):
        # sayim hareketi de stoka ekleme (düzeltme girişi)
        giris = self.hareketler.filter(tip__in=["giris", "sayim"]).aggregate(t=Sum("miktar"))["t"] or 0
        cikis = self.hareketler.filter(tip="cikis").aggregate(t=Sum("miktar"))["t"] or 0
        return giris - cikis

    @property
    def kritik_stok_mu(self):
        return self.min_stok > 0 and self.mevcut_stok <= self.min_stok

    def save(self, *args, **kwargs):
        if not self.kod:
            # Otomatik kod: UR0001, UR0002, ...
            super().save(*args, **kwargs)
            if not self.kod:
                self.kod = f"UR{self.pk:04d}"
                Urun.objects.filter(pk=self.pk).update(kod=self.kod)
        else:
            super().save(*args, **kwargs)


class StokHareketi(models.Model):
    TIP = [
        ("giris", "Giriş"),
        ("cikis", "Çıkış"),
        ("sayim", "Sayım Düzeltme"),
    ]

    urun = models.ForeignKey(
        Urun,
        on_delete=models.PROTECT,
        related_name="hareketler",
        verbose_name="Ürün",
    )
    tarih = models.DateField("Tarih")
    tip = models.CharField("Hareket Tipi", max_length=10, choices=TIP)
    miktar = models.DecimalField("Miktar", max_digits=10, decimal_places=3)
    birim_fiyat = models.DecimalField(
        "Birim Fiyat", max_digits=14, decimal_places=2, default=0, blank=True
    )
    belge_no = models.CharField("Belge No", max_length=50, blank=True)
    aciklama = models.CharField("Açıklama", max_length=300, blank=True)
    olusturuldu = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-tarih", "-olusturuldu"]
        verbose_name = "Stok Hareketi"
        verbose_name_plural = "Stok Hareketleri"

    def __str__(self):
        return f"{self.get_tip_display()} — {self.urun} — {self.miktar} {self.urun.birim}"
