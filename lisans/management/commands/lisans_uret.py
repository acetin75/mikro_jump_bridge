"""
Lisans anahtarı üretme yönetim komutu.

Kullanım (geliştirici ortamında, .env'de LISANS_IMZA_ANAHTARI tanımlıyken):
    python manage.py lisans_uret FIRMA001 2027-05-24
    python manage.py lisans_uret FIRMA001 2027-05-24 --tip premium

Not: Bu komutu sadece geliştirici çalıştırmalıdır.
     Müşteriye yalnızca üretilen ANAHTAR verilir, imzalama anahtarı paylaşılmaz.
"""
from django.core.management.base import BaseCommand

from lisans.utils import lisans_anahtari_uret


class Command(BaseCommand):
    help = "Müşteri için lisans anahtarı üretir."

    def add_arguments(self, parser):
        parser.add_argument("musteri_kodu", type=str, help="Müşteri kodu (örn: FIRMA001)")
        parser.add_argument(
            "bitis_tarihi",
            type=str,
            help="Lisans bitiş tarihi YYYY-AA-GG formatında (örn: 2027-05-24)",
        )
        parser.add_argument(
            "--tip",
            default="standart",
            choices=["standart", "premium"],
            help="Lisans tipi (varsayılan: standart)",
        )

    def handle(self, *args, **options):
        musteri  = options["musteri_kodu"]
        bitis    = options["bitis_tarihi"]
        tip      = options["tip"]
        anahtar  = lisans_anahtari_uret(musteri, bitis, tip)

        self.stdout.write(self.style.SUCCESS("\n========== LİSANS ANAHTARI =========="))
        self.stdout.write(f"Müşteri : {musteri}")
        self.stdout.write(f"Bitiş   : {bitis}")
        self.stdout.write(f"Tip     : {tip}")
        self.stdout.write(self.style.WARNING(f"\nAnahtar :\n{anahtar}"))
        self.stdout.write(self.style.SUCCESS("=====================================\n"))
        self.stdout.write("Bu anahtarı müşteriye gönderin.")
        self.stdout.write("İmzalama anahtarını (LISANS_IMZA_ANAHTARI) ASLA paylaşmayın.\n")
