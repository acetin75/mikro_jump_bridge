import logging
import ssl

from django.core.mail import EmailMessage
from django.core.mail.backends.smtp import EmailBackend as _DjangoSMTP
from django.core.mail.utils import DNS_NAME
from django.template.loader import render_to_string

from .models import EkstreGonderimLog, MailAyar

logger = logging.getLogger("mikro_sync")


def mail_ayar_al() -> MailAyar | None:
    """Aktif mail ayarını döndürür, yoksa None."""
    return MailAyar.objects.filter(aktif=True).first()


class _EsnekSMTPBackend(_DjangoSMTP):
    """SMTP backend; ``MailAyar.tls_dogrulamayi_atla=True`` ise sertifika
    doğrulamasını devre dışı bırakır.

    Varsayılan davranış güvenlidir (Python ``ssl.create_default_context``
    sertifika ve hostname doğrulaması yapar). Yalnızca paylaşımlı/eski
    hosting sunucuları için bilinçli kapatma seçeneği sunar.
    """

    def __init__(self, *args, dogrulamayi_atla: bool = False, **kwargs):
        self._dogrulamayi_atla = dogrulamayi_atla
        super().__init__(*args, **kwargs)

    def open(self):
        if self.connection:
            return False
        ctx = ssl.create_default_context()
        if self._dogrulamayi_atla:
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        connection_params = {"local_hostname": DNS_NAME.get_fqdn()}
        if self.timeout is not None:
            connection_params["timeout"] = self.timeout
        if self.use_ssl:
            connection_params["context"] = ctx
        try:
            self.connection = self.connection_class(
                self.host, self.port, **connection_params
            )
            if not self.use_ssl and self.use_tls:
                self.connection.ehlo()
                self.connection.starttls(context=ctx)
                self.connection.ehlo()
            if self.username and self.password:
                self.connection.login(self.username, self.password)
            return True
        except OSError:
            if not self.fail_silently:
                raise
        return False


def _smtp_baglantisi(ayar: MailAyar):
    """Verilen MailAyar ile SMTP bağlantısı oluşturur."""
    backend = _EsnekSMTPBackend(
        host=ayar.smtp_sunucu,
        port=ayar.smtp_port,
        username=ayar.kullanici,
        password=ayar.sifre_al(),
        use_tls=ayar.tls_kullan,
        fail_silently=False,
        dogrulamayi_atla=ayar.tls_dogrulamayi_atla,
    )
    return backend


def ekstre_gonder(
    *,
    firma_ayar,
    cari_kod: str,
    cari_unvan: str,
    alici_email: list[str] | str,
    bilgi_email: list[str] | None = None,
    donem_baslangic,
    donem_bitis,
    hareketler: list,
    acilis_bakiye=0,
    konu: str = "",
) -> EkstreGonderimLog:
    """
    Ekstre e-postasını gönderir, EkstreGonderimLog kaydeder ve döndürür.
    Hata durumunda log yine kaydedilir; exception yeniden fırlatılır.
    """
    ayar = mail_ayar_al()
    if not ayar:
        raise ValueError(
            "Aktif mail ayarı bulunamadı. "
            "Lütfen /posta/ sayfasından SMTP bilgilerini girin."
        )

    # alici_email listesi veya tekli string kabul eder
    if isinstance(alici_email, str):
        alici_email = [alici_email]
    bilgi_email = bilgi_email or []
    alici_str = ", ".join(alici_email)
    bilgi_str = ", ".join(bilgi_email)

    if not konu:
        konu = (
            f"{cari_unvan} — Hesap Ekstresi "
            f"{donem_baslangic:%d.%m.%Y} – {donem_bitis:%d.%m.%Y}"
        )

    icerik = render_to_string(
        "posta/ekstre_mail.html",
        {
            "firma_ad": firma_ayar.ad,
            "cari_kod": cari_kod,
            "cari_unvan": cari_unvan,
            "donem_baslangic": donem_baslangic,
            "donem_bitis": donem_bitis,
            "hareketler": hareketler,
            "acilis_bakiye": acilis_bakiye,
        },
    )

    log = EkstreGonderimLog(
        firma_ayar=firma_ayar,
        cari_kod=cari_kod,
        cari_unvan=cari_unvan,
        alici_email=alici_str,
        bilgi_email=bilgi_str,
        donem_baslangic=donem_baslangic,
        donem_bitis=donem_bitis,
        konu=konu,
    )

    try:
        connection = _smtp_baglantisi(ayar)
        msg = EmailMessage(
            subject=konu,
            body=icerik,
            from_email=ayar.gonderici,
            to=alici_email,
            cc=bilgi_email if bilgi_email else None,
            connection=connection,
        )
        msg.content_subtype = "html"
        msg.send()
        log.durum = "gonderildi"
        logger.info(
            "Ekstre gönderildi: %s → TO:%s CC:%s",
            cari_kod, alici_str, bilgi_str or "-",
        )
    except Exception as e:
        log.durum = "hata"
        log.hata_mesaji = str(e)
        logger.error(
            "Ekstre gönderim hatası %s → %s: %s", cari_kod, alici_email, e, exc_info=True
        )
        log.save()
        raise
    else:
        log.save()

    return log


def test_maili_gonder(ayar: MailAyar, alici_email: str) -> None:
    """SMTP bağlantısını doğrulamak için basit bir test maili gönderir."""
    connection = _smtp_baglantisi(ayar)
    msg = EmailMessage(
        subject="Mikro Jump Bridge — SMTP Bağlantı Testi",
        body=(
            "<p>Bu e-posta, SMTP bağlantısını doğrulamak için "
            "Mikro Jump Bridge tarafından gönderilmiştir.</p>"
            "<p>Bu mesajı aldıysanız yapılandırma doğrudur.</p>"
        ),
        from_email=ayar.gonderici,
        to=[alici_email],
        connection=connection,
    )
    msg.content_subtype = "html"
    msg.send()
    logger.info("Test maili gönderildi → %s", alici_email)
