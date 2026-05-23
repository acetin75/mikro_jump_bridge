from django.db import models
from cari.models import Cari


class CekSenet(models.Model):
    TIP = [("alınan", "Alınan"), ("verilen", "Verilen")]
    DURUM = [
        ("beklemede", "Beklemede"),
        ("tahsil_edildi", "Tahsil Edildi"),
        ("iade", "İade"),
        ("protestolu", "Protestolu"),
    ]

    cari = models.ForeignKey(
        Cari, on_delete=models.PROTECT, related_name="ceksenets"
    )
    tip = models.CharField(max_length=10, choices=TIP)
    belge_no = models.CharField(max_length=50, verbose_name="Çek/Senet No")
    tutar = models.DecimalField(max_digits=14, decimal_places=2)
    vade_tarihi = models.DateField(verbose_name="Vade Tarihi")
    kesildi_tarihi = models.DateField(null=True, blank=True, verbose_name="Kesildiği Tarih")
    banka_sube = models.CharField(max_length=120, blank=True, verbose_name="Banka/Şube")
    durum = models.CharField(max_length=20, choices=DURUM, default="beklemede")
    notlar = models.TextField(blank=True)
    olusturuldu = models.DateTimeField(auto_now_add=True)
    guncellendi = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["vade_tarihi"]
        verbose_name = "Çek/Senet"
        verbose_name_plural = "Çek/Senetler"

    def __str__(self):
        return f"{self.get_tip_display()} – {self.belge_no} ({self.tutar} ₺)"

    @property
    def vadesi_gecti_mi(self):
        from django.utils import timezone
        return self.durum == "beklemede" and self.vade_tarihi < timezone.now().date()
