from datetime import date

from django.db import models

DENEME_GUN = 15


class LisansBilgisi(models.Model):
    TIP = [
        ("deneme",   "Deneme (15 Gün)"),
        ("standart", "Standart"),
        ("premium",  "Premium"),
    ]

    install_tarihi  = models.DateField("Kurulum Tarihi", auto_now_add=True)
    lisans_tipi     = models.CharField("Lisans Tipi", max_length=20, choices=TIP, default="deneme")
    lisans_anahtari = models.CharField("Lisans Anahtarı", max_length=500, blank=True)
    musteri_kodu    = models.CharField("Müşteri Kodu", max_length=100, blank=True)
    lisans_bitis    = models.DateField("Lisans Bitiş Tarihi", null=True, blank=True)
    guncellendi     = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Lisans Bilgisi"
        verbose_name_plural = "Lisans Bilgileri"

    def __str__(self):
        return f"Lisans [{self.get_lisans_tipi_display()}] — {self.gecerlilik_durumu}"

    # ------------------------------------------------------------------
    @property
    def kalan_gun(self) -> int:
        today = date.today()
        if self.lisans_tipi == "deneme":
            return max(0, DENEME_GUN - (today - self.install_tarihi).days)
        if self.lisans_bitis:
            return max(0, (self.lisans_bitis - today).days)
        return 9999  # süresiz lisans

    @property
    def gecerli_mi(self) -> bool:
        return self.kalan_gun > 0

    @property
    def gecerlilik_durumu(self) -> str:
        if not self.gecerli_mi:
            return "⛔ Süresi Doldu"
        if self.lisans_tipi == "deneme":
            return f"🕐 Deneme — {self.kalan_gun} gün kaldı"
        if self.lisans_bitis:
            return f"✅ Aktif — {self.kalan_gun} gün kaldı"
        return "✅ Aktif — Süresiz"

    @property
    def uyari_seviyesi(self) -> str:
        """Bootstrap renk sınıfı için."""
        if not self.gecerli_mi:
            return "danger"
        if self.lisans_tipi == "deneme":
            return "warning" if self.kalan_gun <= 5 else "info"
        return "success" if self.kalan_gun > 30 else "warning"
