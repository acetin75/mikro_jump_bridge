"""baslat.bat tarafından çağrılır: admin kullanıcıyı yoksa oluşturur ve grupları hazırlar."""
import django
import os
import secrets
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "muhasebe_buro.settings")
django.setup()

from django.contrib.auth.models import Group, User

# Admin kullanıcı — ilk kurulumda rastgele parola üretilir.
# Sonraki başlatmalarda mevcut kullanıcıya dokunulmaz.
if not User.objects.filter(username="admin").exists():
    parola = secrets.token_urlsafe(16)
    User.objects.create_superuser("admin", "admin@localhost", parola)
    print("=" * 60)
    print("[OK] Admin kullanici olusturuldu.")
    print(f"     Kullanici: admin")
    print(f"     Parola   : {parola}")
    print("  !! Bu parolayi not alin — bir daha gosterilmeyecek !!")
    print("=" * 60)
else:
    print("[OK] Admin kullanici zaten mevcut.")

# Roller (gruplar)
ROLLER = ["Yönetici", "Muhasebeci", "Görüntüleyici"]
for rol in ROLLER:
    grup, olusturuldu = Group.objects.get_or_create(name=rol)
    if olusturuldu:
        print(f"[OK] Rol olusturuldu: {rol}")
    else:
        print(f"[OK] Rol zaten mevcut: {rol}")
