import logging

from django.core import signing
from django.db import models

logger = logging.getLogger("mikro_sync")


class FirmaAyar(models.Model):
    """Mikro ERP bağlantı ayarları — her firma için ayrı kayıt."""

    BAGLANTI = [
        ("api", "Mikro API (port 8094)"),
        ("sql", "SQL Server (direkt)"),
        ("manuel", "Manuel XML Yükle"),
    ]

    ad = models.CharField("Firma Adı", max_length=200)
    aktif = models.BooleanField("Aktif", default=True)

    # API bağlantı
    baglanti_tipi = models.CharField(
        "Bağlantı Tipi", max_length=10, choices=BAGLANTI, default="api"
    )
    mikro_sunucu = models.CharField(
        "Yerel LAN IP", max_length=100, blank=True, help_text="örn: 192.168.1.10"
    )
    mikro_sunucu_vpn = models.CharField(
        "FortiClient VPN IP", max_length=100, blank=True, help_text="örn: 10.8.0.5"
    )
    mikro_sunucu_uzak = models.CharField(
        "Uzak Masaüstü IP",
        max_length=100,
        blank=True,
        help_text="RDP ile sunucudaysanız genellikle 127.0.0.1",
    )
    mikro_port = models.PositiveIntegerField("API Port", default=8094)
    mikro_kullanici = models.CharField("Mikro Kullanıcı", max_length=100, blank=True)
    _mikro_sifre_sifreli = models.TextField("Şifreli Parola", blank=True)
    firma_kodu = models.CharField(
        "Firma Kodu", max_length=50, blank=True, help_text="Mikro firma kodu (örn: MORE)"
    )
    calisma_yili = models.CharField(
        "Çalışma Yılı", max_length=4, default="2025", help_text="Örn: 2025"
    )
    mikro_api_key = models.TextField("Mikro API Key", blank=True)

    # SQL Server
    sql_sunucu = models.CharField("SQL Sunucu", max_length=100, blank=True)
    sql_veritabani = models.CharField("SQL Veritabanı", max_length=100, blank=True)
    sql_kullanici = models.CharField("SQL Kullanıcı", max_length=100, blank=True)
    _sql_sifre_sifreli = models.TextField("SQL Şifreli Parola", blank=True)

    notlar = models.TextField("Notlar", blank=True)
    olusturuldu = models.DateTimeField(auto_now_add=True)
    guncellendi = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["ad"]
        verbose_name = "Firma Ayarı"
        verbose_name_plural = "Firma Ayarları"

    def __str__(self):
        return f"{self.ad} ({self.get_baglanti_tipi_display()})"

    @property
    def api_url(self):
        return f"http://{self.mikro_sunucu}:{self.mikro_port}/Api/APIMethods"

    def sunucu_al(self, mod: str = "yerel") -> str:
        """Bağlantı moduna göre doğru sunucu IP'sini döndürür."""
        if mod == "vpn" and self.mikro_sunucu_vpn:
            return self.mikro_sunucu_vpn
        if mod == "uzak" and self.mikro_sunucu_uzak:
            return self.mikro_sunucu_uzak
        return self.mikro_sunucu

    @property
    def baglanti_modlari(self):
        """Dolu olan bağlantı seçeneklerini listeler: [(mod_kodu, mod_adi, ip), ...]"""
        modlar = []
        if self.mikro_sunucu:
            modlar.append(("yerel", "Yerel LAN", self.mikro_sunucu))
        if self.mikro_sunucu_vpn:
            modlar.append(("vpn", "FortiClient VPN", self.mikro_sunucu_vpn))
        if self.mikro_sunucu_uzak:
            modlar.append(("uzak", "Uzak Masaüstü", self.mikro_sunucu_uzak))
        return modlar

    def sifre_kaydet(self, sifre: str):
        self._mikro_sifre_sifreli = signing.dumps(sifre)

    def sifre_al(self) -> str:
        if not self._mikro_sifre_sifreli:
            return ""
        try:
            return signing.loads(self._mikro_sifre_sifreli)
        except signing.BadSignature:
            logger.error("FirmaAyar pk=%s için şifre çözme başarısız", self.pk)
            return ""

    def sql_sifre_kaydet(self, sifre: str):
        self._sql_sifre_sifreli = signing.dumps(sifre)

    def sql_sifre_al(self) -> str:
        if not self._sql_sifre_sifreli:
            return ""
        try:
            return signing.loads(self._sql_sifre_sifreli)
        except signing.BadSignature:
            return ""


class ImportLog(models.Model):
    """Her import işleminin kayıt defteri."""

    DURUM = [
        ("beklemede", "Beklemede"),
        ("onay_bekliyor", "Onay Bekliyor"),
        ("isleniyor", "İşleniyor"),
        ("tamamlandi", "Tamamlandı"),
        ("kismi", "Kısmi Başarı"),
        ("hata", "Hata"),
        ("iptal", "İptal"),
    ]

    firma_ayar = models.ForeignKey(
        FirmaAyar, on_delete=models.PROTECT, related_name="import_loglari"
    )
    baslangic_tarih = models.DateField("Başlangıç Tarihi", null=True, blank=True)
    bitis_tarih = models.DateField("Bitiş Tarihi", null=True, blank=True)
    durum = models.CharField("Durum", max_length=20, choices=DURUM, default="beklemede")
    cekilen_adet = models.IntegerField("Çekilen Kayıt", default=0)
    aktarilan_adet = models.IntegerField("Aktarılan Kayıt", default=0)
    hata_adet = models.IntegerField("Hatalı Kayıt", default=0)
    hata_detay = models.TextField("Hata Detayı", blank=True)
    baslayan = models.ForeignKey("auth.User", on_delete=models.SET_NULL, null=True, blank=True)
    olusturuldu = models.DateTimeField(auto_now_add=True)
    guncellendi = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-olusturuldu"]
        verbose_name = "Import Logu"
        verbose_name_plural = "Import Logları"

    def __str__(self):
        return f"Import #{self.pk} — {self.firma_ayar.ad} — {self.get_durum_display()}"

    @property
    def basari_yuzdesi(self):
        if self.cekilen_adet == 0:
            return 0
        return round(self.aktarilan_adet / self.cekilen_adet * 100, 1)
