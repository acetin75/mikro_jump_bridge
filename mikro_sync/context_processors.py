from sync_motor.models import FirmaAyar


def hy_aktif_firma(request):
    """
    Tüm şablonlara aktif Hesap Yönetimi firmasını ve firma listesini sağlar.
    Session'dan okunur; giriş yapmış kullanıcılar için çalışır.
    """
    if not request.user.is_authenticated:
        return {}
    firma_id = request.session.get("aktif_firma_id")
    aktif = FirmaAyar.objects.filter(pk=firma_id, aktif=True).first() if firma_id else None
    firmalar = FirmaAyar.objects.filter(aktif=True).order_by("ad")
    return {
        "hy_aktif_firma": aktif,
        "hy_firmalar": firmalar,
    }
