import json
from django.db import models


class MikroFatura(models.Model):
    """
    Mikro'dan çekilen alış/satış faturası — staging alan.
    ham_json: Mikro API'den gelen orijinal veri (değiştirilmez).
    """

    DURUM = [
        ("ham", "Ham — İşlenmedi"),
        ("onay_bekliyor", "Onay Bekliyor"),
        ("islendi", "İşlendi"),
        ("hata", "Hata"),
        ("atla", "Atla"),
    ]

    TIP = [
        ("alis", "Alış Faturası"),
        ("satis", "Satış Faturası"),
    ]

    firma_ayar = models.ForeignKey(
        "sync_motor.FirmaAyar", on_delete=models.PROTECT, related_name="mikro_faturalar"
    )
    # Mikro'dan gelen benzersiz tanımlayıcılar
    fat_guid = models.CharField("Mikro GUID", max_length=100, db_index=True)
    fat_evrak_seri = models.CharField("Evrak Seri", max_length=20, blank=True)
    fat_evrak_sira = models.CharField("Evrak Sıra", max_length=20, blank=True)
    fat_tarih = models.DateField("Fatura Tarihi", null=True, blank=True, db_index=True)
    fat_vade_tarihi = models.DateField("Vade Tarihi", null=True, blank=True)

    # Cari bilgileri
    fat_cari_kod = models.CharField("Mikro Cari Kodu", max_length=50, blank=True, db_index=True)
    fat_cari_unvan = models.CharField("Cari Ünvanı", max_length=300, blank=True)
    fat_cari_vkn = models.CharField("Vergi No", max_length=20, blank=True)

    # Tutar
    fat_kdv_haric = models.DecimalField("KDV Hariç", max_digits=14, decimal_places=2, null=True, blank=True)
    fat_kdv = models.DecimalField("KDV Tutarı", max_digits=14, decimal_places=2, null=True, blank=True)
    fat_toplam = models.DecimalField("Genel Toplam", max_digits=14, decimal_places=2, null=True, blank=True)

    # Tip ve durum
    tip = models.CharField("Tip", max_length=5, choices=TIP, default="alis")
    durum = models.CharField("Durum", max_length=20, choices=DURUM, default="ham", db_index=True)

    # Ham veri (dokunulmaz)
    ham_json = models.TextField("Ham JSON", blank=True)

    # İşlem sonucu
    hata_mesaji = models.TextField("Hata Mesajı", blank=True)

    import_log = models.ForeignKey(
        "sync_motor.ImportLog", on_delete=models.SET_NULL, null=True, blank=True, related_name="faturalar"
    )

    olusturuldu = models.DateTimeField(auto_now_add=True)
    guncellendi = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("firma_ayar", "fat_guid")]
        ordering = ["-fat_tarih", "-olusturuldu"]
        verbose_name = "Mikro Fatura"
        verbose_name_plural = "Mikro Faturalar"

    def __str__(self):
        evrak = f"{self.fat_evrak_seri}{self.fat_evrak_sira}" or self.fat_guid[:8]
        return f"{evrak} — {self.fat_cari_unvan}"

    @property
    def ham_veri(self):
        """ham_json'u dict olarak döndürür."""
        if self.ham_json:
            try:
                return json.loads(self.ham_json)
            except (json.JSONDecodeError, TypeError):
                return {}
        return {}

    @property
    def satirlar(self):
        """Fatura satırlarını döndürür (ham_json içindeki liste)."""
        return self.ham_veri.get("satirlar", [])

    @property
    def islendi_mi(self):
        return self.durum == "islendi"


class MikroCariHesap(models.Model):
    """Mikro'dan çekilen cari hesap — eşleştirme için referans."""
    firma_ayar = models.ForeignKey(
        "sync_motor.FirmaAyar", on_delete=models.CASCADE, related_name="cari_hesaplar"
    )
    cari_kod = models.CharField("Cari Kodu", max_length=50)
    cari_unvan = models.CharField("Ünvanı", max_length=300)
    cari_vkn = models.CharField("Vergi No", max_length=20, blank=True)
    cari_telefon = models.CharField("Telefon", max_length=30, blank=True)
    cari_email = models.CharField("E-posta", max_length=100, blank=True)
    guncel_bakiye = models.DecimalField("Güncel Bakiye", max_digits=14, decimal_places=2, null=True, blank=True)
    son_guncelleme = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("firma_ayar", "cari_kod")]
        ordering = ["cari_unvan"]
        verbose_name = "Mikro Cari Hesap"
        verbose_name_plural = "Mikro Cari Hesaplar"

    def __str__(self):
        return f"{self.cari_kod} — {self.cari_unvan}"


class MikroStokKarti(models.Model):
    """Mikro'dan çekilen stok kartı — eşleştirme için referans."""
    firma_ayar = models.ForeignKey(
        "sync_motor.FirmaAyar", on_delete=models.CASCADE, related_name="stok_kartlari"
    )
    stok_kod = models.CharField("Stok Kodu", max_length=50)
    stok_isim = models.CharField("Stok İsmi", max_length=300)
    stok_birimi = models.CharField("Birimi", max_length=20, blank=True)
    satis_fiyati = models.DecimalField("Satış Fiyatı", max_digits=14, decimal_places=4, null=True, blank=True)
    son_guncelleme = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("firma_ayar", "stok_kod")]
        ordering = ["stok_isim"]
        verbose_name = "Mikro Stok Kartı"
        verbose_name_plural = "Mikro Stok Kartları"

    def __str__(self):
        return f"{self.stok_kod} — {self.stok_isim}"
