"""
Lisans anahtarı üretme ve doğrulama yardımcıları.

Anahtar formatı: BASE64URL( musteri|bitis|tip|HMAC-SHA256 )

Güvenlik notu:
  İmzalama anahtarı .env'de LISANS_IMZA_ANAHTARI olarak saklanır.
  Müşteriye sadece lisans anahtarı verilir; imzalama anahtarı paylaşılmaz.
  Anahtarı yalnızca geliştirici üretebilir.
"""
import base64
import hashlib
import hmac
from datetime import date


def _imza_anahtari() -> bytes:
    """İmzalama anahtarını döndürür — .env'den okunur."""
    from decouple import config, UndefinedValueError
    try:
        return config("LISANS_IMZA_ANAHTARI").encode()
    except UndefinedValueError:
        # .env tanımlı değilse Django SECRET_KEY'den türet
        from django.conf import settings
        return hashlib.sha256(
            (settings.SECRET_KEY + "-lisans").encode()
        ).digest()


def lisans_anahtari_uret(musteri_kodu: str, bitis_tarihi: str, tip: str = "standart") -> str:
    """
    Müşteriye verilecek lisans anahtarı üretir.

    Kullanım (yönetim komutu ile):
        python manage.py lisans_uret FIRMA001 2027-05-24
        python manage.py lisans_uret FIRMA001 2027-05-24 --tip premium
    """
    payload = f"{musteri_kodu}|{bitis_tarihi}|{tip}"
    imza = hmac.new(_imza_anahtari(), payload.encode(), hashlib.sha256).hexdigest()
    raw = f"{payload}|{imza}"
    return base64.urlsafe_b64encode(raw.encode()).decode()


def lisans_anahtari_dogrula(anahtar: str) -> dict | None:
    """
    Lisans anahtarını doğrular.

    Geçerliyse: {"musteri": str, "bitis": date, "tip": str}
    Geçersizse: None
    """
    try:
        decoded = base64.urlsafe_b64decode(anahtar.encode()).decode()
        parts = decoded.split("|")
        if len(parts) != 4:
            return None
        musteri, bitis_str, tip, received_imza = parts
        payload = f"{musteri}|{bitis_str}|{tip}"
        expected_imza = hmac.new(
            _imza_anahtari(), payload.encode(), hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(received_imza, expected_imza):
            return None
        bitis = date.fromisoformat(bitis_str)
        if bitis < date.today():
            return None  # Süresi geçmiş anahtar
        return {"musteri": musteri, "bitis": bitis, "tip": tip}
    except Exception:
        return None
