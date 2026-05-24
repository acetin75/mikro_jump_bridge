import logging

from django.core.mail import EmailMessage, get_connection
from django.template.loader import render_to_string

from .models import EkstreGonderimLog, MailAyar

logger = logging.getLogger("mikro_sync")


def mail_ayar_al() -> MailAyar | None:
    """Aktif mail ayarını döndürür, yoksa None."""
    return MailAyar.objects.filter(aktif=True).first()


def _smtp_baglantisi(ayar: MailAyar):
    """Verilen MailAyar ile SMTP bağlantısı oluşturur."""
    return get_connection(
        backend="django.core.mail.backends.smtp.EmailBackend",
        host=ayar.smtp_sunucu,
        port=ayar.smtp_port,
        username=ayar.kullanici,
        password=ayar.sifre_al(),
        use_tls=ayar.tls_kullan,
        fail_silently=False,
    )


def ekstre_gonder(
    *,
    firma_ayar,
    cari_kod: str,
    cari_unvan: str,
    alici_email: str,
    donem_baslangic,
    donem_bitis,
    hareketler: list,
    acilis_bakiye: float = 0.0,
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
        alici_email=alici_email,
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
            to=[alici_email],
            connection=connection,
        )
        msg.content_subtype = "html"
        msg.send()
        log.durum = "gonderildi"
        logger.info("Ekstre gönderildi: %s → %s", cari_kod, alici_email)
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
