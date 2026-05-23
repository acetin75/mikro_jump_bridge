"""
Çek/Senet vade hatırlatma e-postası gönderir.

Kullanım:
    python manage.py hatirlatma_gonder           # 7 gün içinde vadeliler
    python manage.py hatirlatma_gonder --gun 14  # 14 gün içinde vadeliler
    python manage.py hatirlatma_gonder --vadesi_gecenler  # Sadece vadesi geçenler

Zamanlanmış görev örneği (Windows Görev Zamanlayıcı / cron):
    python manage.py hatirlatma_gonder --gun 7

E-posta ayarı için settings.py'de EMAIL_HOST, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD,
EMAIL_PORT, EMAIL_USE_TLS değerlerini ve HATIRLATMA_ALICI listesini doldurun.
"""

from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings


class Command(BaseCommand):
    help = "Vadesi yaklaşan veya geçen çek/senet hatırlatma e-postası gönderir."

    def add_arguments(self, parser):
        parser.add_argument(
            "--gun",
            type=int,
            default=7,
            help="Kaç gün içinde vadeye girecek olanları gönder (varsayılan: 7)",
        )
        parser.add_argument(
            "--vadesi_gecenler",
            action="store_true",
            help="Sadece vadesi geçmiş bekleyen kayıtları gönder",
        )

    def handle(self, *args, **options):
        from ceksenet.models import CekSenet

        bugun = timezone.now().date()
        gun = options["gun"]
        hedef_gun = bugun + timezone.timedelta(days=gun)

        if options["vadesi_gecenler"]:
            qs = CekSenet.objects.filter(
                durum="beklemede", vade_tarihi__lt=bugun
            ).select_related("cari")
            konu_ek = "VADESİ GEÇMİŞ"
        else:
            qs = CekSenet.objects.filter(
                durum="beklemede",
                vade_tarihi__gte=bugun,
                vade_tarihi__lte=hedef_gun,
            ).select_related("cari")
            konu_ek = f"{gun} GÜN İÇİNDE VADELİ"

        if not qs.exists():
            self.stdout.write(self.style.SUCCESS("Gönderilecek hatırlatma yok."))
            return

        satirlar = []
        for cs in qs:
            satirlar.append(
                f"  • [{cs.get_tip_display()}] {cs.belge_no} — {cs.cari.ad} "
                f"| Tutar: {cs.tutar} ₺ | Vade: {cs.vade_tarihi} | Banka: {cs.banka_sube or '-'}"
            )
        icerik = (
            f"Muhasebe Bürosu — Çek/Senet Hatırlatma ({konu_ek})\n"
            f"Rapor Tarihi: {bugun}\n"
            f"Kayıt Sayısı : {qs.count()}\n\n"
            + "\n".join(satirlar)
        )

        alicilar = getattr(settings, "HATIRLATMA_ALICI", [])
        if not alicilar:
            self.stdout.write(
                self.style.WARNING(
                    "settings.py'de HATIRLATMA_ALICI listesi tanımlı değil. "
                    "E-posta gönderilemedi.\n\n" + icerik
                )
            )
            return

        send_mail(
            subject=f"[Muhasebe] Çek/Senet Hatırlatma — {konu_ek} ({qs.count()} kayıt)",
            message=icerik,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@muhasebe.local"),
            recipient_list=alicilar,
            fail_silently=False,
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"{qs.count()} kayıt için hatırlatma e-postası {alicilar} adresine gönderildi."
            )
        )
