"""
Fatura vade hatırlatma e-postası gönderir.

Kullanım:
    python manage.py fatura_hatirlatma           # 7 gün içinde vadesi dolacaklar
    python manage.py fatura_hatirlatma --gun 14  # 14 gün içinde vadesi dolacaklar
    python manage.py fatura_hatirlatma --vadesi_gecenler  # Sadece vadesi geçenler

Zamanlanmış görev örneği (Windows Görev Zamanlayıcı):
    schtasks /create /tn "FaturaHatirlatma" /tr "C:\\muhasebe_buro\\.venv\\Scripts\\python.exe C:\\muhasebe_buro\\manage.py fatura_hatirlatma --gun 7" /sc DAILY /st 09:00

E-posta ayarı için .env dosyasında EMAIL_HOST_USER, EMAIL_HOST_PASSWORD ve
HATIRLATMA_ALICI değerlerini doldurun.
"""

import logging

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.utils import timezone

logger = logging.getLogger("muhasebe")


class Command(BaseCommand):
    help = "Vadesi yaklaşan veya geçen faturalar için hatırlatma e-postası gönderir."

    def add_arguments(self, parser):
        parser.add_argument(
            "--gun",
            type=int,
            default=7,
            help="Kaç gün içinde vadesi dolacak faturaları gönder (varsayılan: 7)",
        )
        parser.add_argument(
            "--vadesi_gecenler",
            action="store_true",
            help="Sadece vadesi geçmiş ödenmemiş faturaları gönder",
        )

    def handle(self, *args, **options):
        from fatura.models import Fatura

        bugun = timezone.now().date()
        gun = options["gun"]
        hedef_gun = bugun + timezone.timedelta(days=gun)

        # Sadece kesildi durumundaki satış faturaları takip edilir
        if options["vadesi_gecenler"]:
            faturalar = [
                f for f in Fatura.objects.filter(
                    tip="satis", durum="kesildi",
                ).select_related("cari")
                if f.vade_tarihi and f.vade_tarihi < bugun
            ]
            konu_ek = "VADESİ GEÇMİŞ FATURALAR"
        else:
            faturalar = [
                f for f in Fatura.objects.filter(
                    tip="satis", durum="kesildi",
                    vade_tarihi__gte=bugun,
                    vade_tarihi__lte=hedef_gun,
                ).select_related("cari")
            ]
            konu_ek = f"{gun} GÜN İÇİNDE VADESİ DOLACAK FATURALAR"

        if not faturalar:
            self.stdout.write(self.style.SUCCESS("Gönderilecek fatura hatırlatması yok."))
            return

        satirlar = []
        for f in sorted(faturalar, key=lambda x: x.vade_tarihi or bugun):
            satirlar.append(
                f"  • {f.fatura_no} — {f.cari.ad} "
                f"| Tutar: {f.genel_toplam} ₺ | Vade: {f.vade_tarihi}"
            )

        icerik = (
            f"Muhasebe Bürosu — Fatura Hatırlatma ({konu_ek})\n"
            f"Rapor Tarihi : {bugun}\n"
            f"Fatura Sayısı: {len(faturalar)}\n\n"
            + "\n".join(satirlar)
        )

        alicilar = getattr(settings, "HATIRLATMA_ALICI", [])
        if not alicilar:
            self.stdout.write(
                self.style.WARNING(
                    ".env dosyasında HATIRLATMA_ALICI tanımlı değil. "
                    "E-posta gönderilemedi.\n\n" + icerik
                )
            )
            return

        try:
            send_mail(
                subject=f"[Muhasebe Bürosu] {konu_ek} — {bugun}",
                message=icerik,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=alicilar,
                fail_silently=False,
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"{len(faturalar)} fatura hatırlatması {', '.join(alicilar)} adresine gönderildi."
                )
            )
            logger.info("Fatura hatırlatma gönderildi: %d fatura, alıcılar: %s", len(faturalar), alicilar)
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"E-posta gönderilemedi: {e}"))
            logger.error("Fatura hatırlatma e-postası gönderilemedi: %s", e, exc_info=True)
