import logging

from django.core.signing import BadSignature, Signer
from django.db import models

logger = logging.getLogger("mikro_sync")


class MailAyar(models.Model):
    """
    Giden posta (SMTP) yapılandırması.
    Singleton gibi kullanılır — aktif=True olan ilk kayıt geçerlidir.
    Şifre django.core.signing.Signer ile şifrelenir, ham değer DB'ye yazılmaz.
    """

    smtp_sunucu = models.CharField("SMTP Sunucusu", max_length=200)
    smtp_port = models.PositiveSmallIntegerField("SMTP Port", default=587)
    kullanici = models.EmailField("Kullanıcı Adı (E-posta)")
    _sifre_sifreli = models.TextField(
        "Şifre (Şifreli)", blank=True, db_column="sifre_sifreli"
    )
    tls_kullan = models.BooleanField("TLS Kullan", default=True)
    tls_dogrulamayi_atla = models.BooleanField(
        "TLS Sertifika Doğrulamasını Atla",
        default=False,
        help_text="Yalnızca paylaşımlı/eski hosting sunucularında "
                  "CERTIFICATE_VERIFY_FAILED hatası alındığında işaretleyin. "
                  "Bağlantı şifreli kalır ancak sunucu kimliği doğrulanmaz.",
    )
    gonderen_ad = models.CharField("Gönderici Adı", max_length=200, blank=True)
    gonderen_email = models.EmailField("Gönderici E-posta", blank=True)
    aktif = models.BooleanField("Aktif", default=True)
    guncellendi = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-guncellendi"]
        verbose_name = "Mail Ayarı"
        verbose_name_plural = "Mail Ayarları"

    def __str__(self):
        return f"{self.kullanici} ({self.smtp_sunucu}:{self.smtp_port})"

    def sifre_kaydet(self, sifre: str) -> None:
        """Ham şifreyi imzalayarak kaydeder."""
        self._sifre_sifreli = Signer().sign(sifre) if sifre else ""

    def sifre_al(self) -> str:
        """İmzalı şifreyi çözüp döndürür."""
        if not self._sifre_sifreli:
            return ""
        try:
            return Signer().unsign(self._sifre_sifreli)
        except BadSignature:
            logger.error("MailAyar şifre çözme hatası (BadSignature)")
            return ""

    @property
    def gonderici(self) -> str:
        """E-posta gönderici başlığı: 'Ad Soyad <eposta@domain.com>'"""
        ad = self.gonderen_ad or ""
        eposta = self.gonderen_email or self.kullanici
        return f"{ad} <{eposta}>" if ad else eposta


class EkstreGonderimLog(models.Model):
    """Her ekstre gönderim denemesinin kaydı."""

    DURUM = [
        ("gonderildi", "Gönderildi"),
        ("hata", "Hata"),
    ]

    firma_ayar = models.ForeignKey(
        "sync_motor.FirmaAyar",
        on_delete=models.PROTECT,
        verbose_name="Firma",
    )
    cari_kod = models.CharField("Cari Kodu", max_length=50)
    cari_unvan = models.CharField("Cari Ünvanı", max_length=300, blank=True)
    alici_email = models.CharField("Alıcı (TO)", max_length=500)
    bilgi_email = models.CharField("Bilgi (CC)", max_length=500, blank=True)
    donem_baslangic = models.DateField("Dönem Başlangıcı")
    donem_bitis = models.DateField("Dönem Bitişi")
    konu = models.CharField("Konu", max_length=300, blank=True)
    durum = models.CharField("Durum", max_length=20, choices=DURUM, default="gonderildi")
    hata_mesaji = models.TextField("Hata Mesajı", blank=True)
    olusturuldu = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-olusturuldu"]
        verbose_name = "Ekstre Gönderim Logu"
        verbose_name_plural = "Ekstre Gönderim Logları"

    def __str__(self):
        return f"{self.cari_kod} → {self.alici_email} ({self.get_durum_display()})"
