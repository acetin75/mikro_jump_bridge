import uuid

from django.db import models
from django.utils import timezone


KDV_ORANLARI = [(0, "%0"), (1, "%1"), (8, "%8"), (10, "%10"), (20, "%20")]


def fatura_no_uret(tip):
    """Yıl + sıra numarasından fatura no üretir: SAT-2026-0001 / ALI-2026-0001"""
    yil = timezone.now().year
    prefix = "SAT" if tip == "satis" else "ALI"
    son = (
        Fatura.objects.filter(tip=tip, tarih__year=yil)
        .order_by("-fatura_no")
        .values_list("fatura_no", flat=True)
        .first()
    )
    if son:
        try:
            num = int(son.rsplit("-", 1)[-1]) + 1
        except ValueError:
            num = 1
    else:
        num = 1
    return f"{prefix}-{yil}-{num:04d}"


class Fatura(models.Model):
    TIP = [("satis", "Satış (Müşteriye)"), ("alis", "Alış (Tedarikçiden)")]
    DURUM = [
        ("taslak", "Taslak"),
        ("kesildi", "Kesildi"),
        ("odendi", "Ödendi"),
        ("iptal", "İptal"),
    ]
    E_FATURA_DURUM = [
        ("yok", "E-Fatura Değil"),
        ("hazir", "XML Hazır"),
        ("yuklendi", "GİB'e Yüklendi"),
        ("onaylandi", "Onaylandı"),
    ]

    fatura_no = models.CharField("Fatura No", max_length=30, blank=True)
    cari = models.ForeignKey(
        "cari.Cari", on_delete=models.PROTECT, related_name="faturalar", verbose_name="Cari"
    )
    tip = models.CharField("Tip", max_length=10, choices=TIP, default="satis")
    durum = models.CharField("Durum", max_length=15, choices=DURUM, default="taslak")
    tarih = models.DateField("Fatura Tarihi")
    vade_tarihi = models.DateField("Vade Tarihi", null=True, blank=True)
    aciklama = models.CharField("Açıklama / Konu", max_length=300, blank=True)
    notlar = models.TextField("Notlar", blank=True)
    para_birimi = models.CharField("Para Birimi", max_length=3, default="TRY")
    odeme_yontemi = models.CharField(
        "Ödeme Yöntemi", max_length=20,
        choices=[
            ("nakit", "Nakit"),
            ("havale", "Havale / EFT"),
            ("kredi_karti", "Kredi Kartı"),
            ("cek", "Çek"),
            ("diger", "Diğer"),
        ],
        default="havale",
        blank=True,
    )
    # E-Fatura alanları
    e_fatura_uuid = models.UUIDField("E-Fatura UUID", default=uuid.uuid4, editable=False, unique=True)
    e_fatura_durum = models.CharField(
        "E-Fatura Durumu", max_length=15, choices=E_FATURA_DURUM, default="yok"
    )
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)
    guncelleme_tarihi = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-tarih", "-olusturma_tarihi"]
        verbose_name = "Fatura"
        verbose_name_plural = "Faturalar"

    def __str__(self):
        return f"{self.fatura_no} — {self.cari.ad}"

    def save(self, *args, **kwargs):
        if not self.fatura_no:
            self.fatura_no = fatura_no_uret(self.tip)
        super().save(*args, **kwargs)

    # ── Hesaplanan alanlar ──────────────────────────────────────────────────

    @property
    def kdv_haric_toplam(self):
        return sum(k.kdv_haric_tutar for k in self.kalemler.all())

    @property
    def kdv_toplam(self):
        return sum(k.kdv_tutari for k in self.kalemler.all())

    @property
    def genel_toplam(self):
        return sum(k.kdv_dahil_tutar for k in self.kalemler.all())

    @property
    def kdv_ozeti(self):
        """KDV oranına göre gruplu özet: {oran: {'matrah': x, 'kdv': y}}"""
        ozet = {}
        for k in self.kalemler.all():
            oran = k.kdv_orani
            if oran not in ozet:
                ozet[oran] = {"matrah": 0, "kdv": 0}
            ozet[oran]["matrah"] += k.kdv_haric_tutar
            ozet[oran]["kdv"] += k.kdv_tutari
        return dict(sorted(ozet.items()))

    @property
    def vadesi_gecti_mi(self):
        if self.vade_tarihi and self.durum not in ("odendi", "iptal"):
            return self.vade_tarihi < timezone.now().date()
        return False


class FaturaKalemi(models.Model):
    fatura = models.ForeignKey(
        Fatura, on_delete=models.CASCADE, related_name="kalemler", verbose_name="Fatura"
    )
    urun = models.ForeignKey(
        "stok.Urun",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Ürün",
        related_name="fatura_kalemleri",
    )
    sira = models.PositiveSmallIntegerField("Sıra", default=1)
    aciklama = models.CharField("Açıklama / Hizmet", max_length=300)
    miktar = models.DecimalField("Miktar", max_digits=10, decimal_places=3, default=1)
    birim = models.CharField("Birim", max_length=20, default="Adet")
    birim_fiyat = models.DecimalField("Birim Fiyat", max_digits=14, decimal_places=2)
    kdv_orani = models.IntegerField("KDV Oranı (%)", choices=KDV_ORANLARI, default=20)
    iskonto_oran = models.DecimalField("İskonto (%)", max_digits=5, decimal_places=2, default=0)

    class Meta:
        ordering = ["sira"]
        verbose_name = "Fatura Kalemi"
        verbose_name_plural = "Fatura Kalemleri"

    def __str__(self):
        return f"{self.fatura.fatura_no} — {self.aciklama}"

    @property
    def kdv_haric_tutar(self):
        from decimal import Decimal
        brut = self.miktar * self.birim_fiyat
        iskonto = brut * self.iskonto_oran / Decimal(100)
        return brut - iskonto

    @property
    def kdv_tutari(self):
        from decimal import Decimal
        return self.kdv_haric_tutar * Decimal(self.kdv_orani) / Decimal(100)

    @property
    def kdv_dahil_tutar(self):
        return self.kdv_haric_tutar + self.kdv_tutari
