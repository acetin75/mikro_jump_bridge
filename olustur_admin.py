"""
Admin kullanıcısı oluşturma scripti.
Çalıştır: .venv\Scripts\python.exe olustur_admin.py

.env dosyasında ADMIN_KULLANICI ve ADMIN_SIFRE tanımlıysa sessiz çalışır.
Tanımlı değilse interaktif olarak sorar.
"""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mikro_sync.settings")
django.setup()

from decouple import config, UndefinedValueError  # noqa: E402
from django.contrib.auth import get_user_model  # noqa: E402

User = get_user_model()

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
    if not password:
        print("Şifre boş olamaz.")
        exit(1)

if User.objects.filter(username=username).exists():
    user = User.objects.get(username=username)
    user.set_password(password)
    user.save()
    print(f"'{username}' kullanıcısının şifresi güncellendi.")
else:
    User.objects.create_superuser(username=username, email=email, password=password)
    print(f"'{username}' admin kullanıcısı oluşturuldu.")

