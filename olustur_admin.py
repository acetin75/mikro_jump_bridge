r"""
Admin kullanıcısı oluşturma scripti.
Çalıştır: .venv\Scripts\python.exe olustur_admin.py

.env dosyasında ADMIN_KULLANICI ve ADMIN_SIFRE tanımlıysa sessiz çalışır.
Tanımlı değilse interaktif olarak sorar.

Zayıf veya yer tutucu şifreler (`admin123`, `buraya-yazin`, vb.) reddedilir.
"""
import os
import sys

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mikro_sync.settings")
django.setup()

from decouple import UndefinedValueError, config  # noqa: E402
from django.contrib.auth import get_user_model  # noqa: E402
from django.contrib.auth.password_validation import validate_password  # noqa: E402
from django.core.exceptions import ValidationError  # noqa: E402

User = get_user_model()

ZAYIF_KALIPLAR = (
    "buraya", "degistir", "değiştir", "change", "changeme",
    "example", "placeholder", "your-password",
)


def sifre_gecerli_mi(username: str, password: str) -> list[str]:
    """Şifre güçlü değilse hata mesajları listesi döner; geçerliyse boş liste."""
    hatalar: list[str] = []
    if not password:
        hatalar.append("Şifre boş olamaz.")
        return hatalar
    dusuk = password.lower()
    for kalip in ZAYIF_KALIPLAR:
        if kalip in dusuk:
            hatalar.append(f"Şifre yer tutucu kalıp içeriyor: '{kalip}'")
            break
    try:
        # Geçici user nesnesi ile UserAttributeSimilarityValidator çalışsın
        validate_password(password, user=User(username=username))
    except ValidationError as e:
        hatalar.extend(e.messages)
    return hatalar


try:
    username = config("ADMIN_KULLANICI", default="admin")
    password = config("ADMIN_SIFRE")
    email = ""
    interactive = False
except UndefinedValueError:
    interactive = True

if interactive:
    username = input("Kullanıcı adı (varsayılan: admin): ").strip() or "admin"
    email = input("E-posta (boş bırakılabilir): ").strip()
    password = input("Şifre: ").strip()

hatalar = sifre_gecerli_mi(username, password)
if hatalar:
    print("HATA: Admin şifresi yeterince güçlü değil:")
    for h in hatalar:
        print(f"  - {h}")
    if not interactive:
        print("Lütfen .env dosyasındaki ADMIN_SIFRE değerini güçlendirin.")
    sys.exit(1)

if User.objects.filter(username=username).exists():
    user = User.objects.get(username=username)
    user.set_password(password)
    user.save()
    print(f"'{username}' kullanıcısının şifresi güncellendi.")
else:
    User.objects.create_superuser(username=username, email=email, password=password)
    print(f"'{username}' admin kullanıcısı oluşturuldu.")

