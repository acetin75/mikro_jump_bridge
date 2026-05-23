from django.db import models


class Cari(models.Model):
    """Müşteri, tedarikçi veya çalışan gibi cari hesap sahibi."""

    TIP = [
        ("musteri", "Müşteri"),
        ("tedarikci", "Tedarikçi"),
        ("diger", "Diğer"),
    ]

    ad = models.CharField("Unvan / Ad Soyad", max_length=200)
    tip = models.CharField("Tip", max_length=20, choices=TIP, default="musteri")
    vergi_no = models.CharField("Vergi / TC No", max_length=20, blank=True)
    vergi_dairesi = models.CharField("Vergi Dairesi", max_length=100, blank=True)
    telefon = models.CharField("Telefon", max_length=30, blank=True)
    email = models.EmailField("E-posta", blank=True)
    adres = models.TextField("Adres", blank=True)
    notlar = models.TextField("Notlar", blank=True)
    aktif = models.BooleanField("Aktif", default=True)
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)
    guncelleme_tarihi = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["ad"]
        verbose_name = "Cari"
        verbose_name_plural = "Cariler"

    def __str__(self):
        return self.ad

    @property
    def bakiye(self):
        """Borç - Alacak = Net bakiye (pozitif = alacak, negatif = borç)."""
        from django.db.models import Sum
        hareketler = self.hareketler.aggregate(
            toplam_borc=Sum("borc"),
            toplam_alacak=Sum("alacak"),
        )
        borc = hareketler["toplam_borc"] or 0
        alacak = hareketler["toplam_alacak"] or 0
        return alacak - borc

    @property
    def toplam_borc(self):
        from django.db.models import Sum
        return self.hareketler.aggregate(Sum("borc"))["borc__sum"] or 0

    @property
    def toplam_alacak(self):
        from django.db.models import Sum
        return self.hareketler.aggregate(Sum("alacak"))["alacak__sum"] or 0


class HesapHareketi(models.Model):
    """Cari hesaba ait tek bir borç veya alacak kalemi."""

    TIP = [
        ("fatura", "Fatura"),
        ("tahsilat", "Tahsilat"),
        ("odeme", "Ödeme"),
        ("iade", "İade"),
        ("duzeltme", "Düzeltme"),
        ("diger", "Diğer"),
    ]

    cari = models.ForeignKey(
        Cari, on_delete=models.PROTECT, related_name="hareketler", verbose_name="Cari"
    )
    tarih = models.DateField("Tarih")
    belge_no = models.CharField("Belge / Fatura No", max_length=50, blank=True)
    aciklama = models.CharField("Açıklama", max_length=300)
    hareket_tipi = models.CharField("Hareket Tipi", max_length=20, choices=TIP, default="diger")
    borc = models.DecimalField("Borç", max_digits=14, decimal_places=2, default=0)
    alacak = models.DecimalField("Alacak", max_digits=14, decimal_places=2, default=0)
    para_birimi = models.CharField("Para Birimi", max_length=3, default="TRY")
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-tarih", "-olusturma_tarihi"]
        verbose_name = "Hesap Hareketi"
        verbose_name_plural = "Hesap Hareketleri"

    def __str__(self):
        return f"{self.cari} | {self.tarih} | {self.aciklama}"
