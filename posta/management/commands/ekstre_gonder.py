"""
Otomatik ekstre gönderim komutu.

Kullanım örnekleri:
  # Tüm aktif firmalar — bu ay
  python manage.py ekstre_gonder

  # Belirli firma — belirli ay
  python manage.py ekstre_gonder --firma 1 --ay 2026-05

  # Manuel tarih aralığı
  python manage.py ekstre_gonder --firma 1 --baslangic 2026-01-01 --bitis 2026-03-31

  # Kuru çalıştırma (gerçekten göndermez, kimlere gideceğini listeler)
  python manage.py ekstre_gonder --firma 1 --ay 2026-05 --kuru

Windows Task Scheduler için:
  C:\\mikro_jump_bridge\\.venv\\Scripts\\python.exe manage.py ekstre_gonder
"""

import calendar
import logging
from datetime import date

from django.core.management.base import BaseCommand, CommandError

from posta.models import MailAyar
from posta.utils import ekstre_gonder
from sync_motor.client import MikroApiClient, MikroApiHatasi
from sync_motor.models import FirmaAyar

logger = logging.getLogger("mikro_sync")

DOVIZ_TL = 0  # cha_d_cins = 0 → Türk Lirası


class Command(BaseCommand):
    help = "Aktif carilere hesap ekstresi e-postası gönderir."

    def add_arguments(self, parser):
        parser.add_argument(
            "--firma",
            type=int,
            default=None,
            help="Firma ID (belirtilmezse tüm aktif firmalar işlenir)",
        )
        parser.add_argument(
            "--ay",
            type=str,
            default=None,
            help="Dönem — YYYY-MM formatında ay (örn. 2026-05)",
        )
        parser.add_argument(
            "--baslangic",
            type=str,
            default=None,
            help="Dönem başlangıç tarihi — YYYY-MM-DD",
        )
        parser.add_argument(
            "--bitis",
            type=str,
            default=None,
            help="Dönem bitiş tarihi — YYYY-MM-DD",
        )
        parser.add_argument(
            "--kuru",
            action="store_true",
            default=False,
            help="Kuru çalıştırma: e-posta göndermez, kimlere gideceğini listeler",
        )

    def handle(self, *args, **options):  # noqa: C901
        # ---------------------------------------------------------------------------
        # Dönem hesapla
        # ---------------------------------------------------------------------------
        baslangic, bitis = self._donem_hesapla(options)

        # ---------------------------------------------------------------------------
        # Mail ayarı kontrol
        # ---------------------------------------------------------------------------
        if not options["kuru"]:
            ayar = MailAyar.objects.filter(aktif=True).first()
            if not ayar:
                raise CommandError(
                    "Aktif mail ayarı bulunamadı. "
                    "python manage.py'yi çalıştırmadan önce /posta/ sayfasından SMTP ayarlayın."
                )

        # ---------------------------------------------------------------------------
        # Firma listesi
        # ---------------------------------------------------------------------------
        if options["firma"]:
            try:
                firmalar = [FirmaAyar.objects.get(pk=options["firma"], aktif=True)]
            except FirmaAyar.DoesNotExist:
                raise CommandError(f"Firma bulunamadı veya pasif: pk={options['firma']}")
        else:
            firmalar = list(FirmaAyar.objects.filter(aktif=True))

        if not firmalar:
            self.stderr.write("Aktif firma bulunamadı.")
            return

        self.stdout.write(
            self.style.SUCCESS(
                f"Dönem: {baslangic:%d.%m.%Y} – {bitis:%d.%m.%Y}  |  "
                f"{len(firmalar)} firma  |  {'KURU ÇALIŞTIRMA' if options['kuru'] else 'GÖNDERME MODU'}"
            )
        )

        toplam_gonderilen = 0
        toplam_hata = 0

        for firma in firmalar:
            g, h = self._firma_isle(firma, baslangic, bitis, options["kuru"])
            toplam_gonderilen += g
            toplam_hata += h

        self.stdout.write(
            self.style.SUCCESS(
                f"\nSonuç — Gönderilen: {toplam_gonderilen}  |  Hata: {toplam_hata}"
            )
        )

    # ---------------------------------------------------------------------------
    # Yardımcılar
    # ---------------------------------------------------------------------------

    def _donem_hesapla(self, options):
        if options["ay"]:
            try:
                yil, ay = map(int, options["ay"].split("-"))
            except (ValueError, AttributeError):
                raise CommandError("--ay YYYY-MM formatında olmalı (örn. 2026-05)")
            son_gun = calendar.monthrange(yil, ay)[1]
            return date(yil, ay, 1), date(yil, ay, son_gun)

        if options["baslangic"] and options["bitis"]:
            try:
                baslangic = date.fromisoformat(options["baslangic"])
                bitis = date.fromisoformat(options["bitis"])
            except ValueError:
                raise CommandError("Tarihler YYYY-MM-DD formatında olmalı")
            return baslangic, bitis

        # Varsayılan: geçen ay
        bugun = date.today()
        ay = bugun.month - 1 or 12
        yil = bugun.year if bugun.month > 1 else bugun.year - 1
        son_gun = calendar.monthrange(yil, ay)[1]
        return date(yil, ay, 1), date(yil, ay, son_gun)

    def _firma_isle(self, firma, baslangic, bitis, kuru):
        self.stdout.write(f"\n▶ {firma.ad}")
        gonderilen = 0
        hata = 0

        try:
            client = MikroApiClient(firma)
            # E-postası olan aktif cariler
            cariler = client.sql_oku("""
                SELECT cari_kod, cari_unvan1, cari_EMail
                FROM CARI_HESAPLAR
                WHERE cari_baglanti_tipi = 0
                  AND cari_EMail IS NOT NULL
                  AND cari_EMail <> ''
                ORDER BY cari_unvan1
            """)
        except MikroApiHatasi as e:
            self.stderr.write(f"  Mikro API hatası ({firma.ad}): {e}")
            return 0, 1

        if not cariler:
            self.stdout.write("  E-posta kayıtlı cari bulunamadı.")
            return 0, 0

        self.stdout.write(f"  {len(cariler)} cari bulundu.")

        for cari in cariler:
            kod = cari.get("cari_kod", "")
            unvan = cari.get("cari_unvan1", "")
            email = (cari.get("cari_EMail") or "").strip()

            if not email:
                continue

            if kuru:
                self.stdout.write(f"  [KURU] {kod} ({unvan}) → {email}")
                continue

            try:
                hareketler, acilis = self._hareketleri_cek(client, kod, baslangic, bitis)

                if not hareketler:
                    self.stdout.write(f"  {kod}: hareket yok, atlandı.")
                    continue

                ekstre_gonder(
                    firma_ayar=firma,
                    cari_kod=kod,
                    cari_unvan=unvan,
                    alici_email=email,
                    donem_baslangic=baslangic,
                    donem_bitis=bitis,
                    hareketler=hareketler,
                    acilis_bakiye=acilis,
                )
                gonderilen += 1
                self.stdout.write(f"  ✓ {kod} → {email}")

            except Exception as e:
                hata += 1
                self.stderr.write(f"  ✗ {kod} → {email}: {e}")

        return gonderilen, hata

    def _hareketleri_cek(self, client, cari_kod, baslangic, bitis):
        temiz_kod = cari_kod.replace("'", "''")

        acilis_sonuc = client.sql_oku(f"""
            SELECT
                SUM(CASE WHEN cha_tip = 0 THEN cha_meblag ELSE -cha_meblag END) AS bakiye
            FROM CARI_HESAP_HAREKETLERI
            WHERE cha_kod = '{temiz_kod}'
              AND cha_iptal = 0
              AND cha_d_cins = {DOVIZ_TL}
              AND cha_tarihi < '{baslangic}'
        """)
        acilis = float((acilis_sonuc[0].get("bakiye") or 0) if acilis_sonuc else 0)

        ham = client.sql_oku(f"""
            SELECT TOP 2000
                cha_tarihi  AS tarih,
                cha_evrakno_seri + '-' + CAST(cha_evrakno_sira AS VARCHAR) AS evrak_no,
                cha_aciklama AS aciklama,
                CASE WHEN cha_tip = 0 THEN cha_meblag ELSE 0 END AS borc,
                CASE WHEN cha_tip = 1 THEN cha_meblag ELSE 0 END AS alacak
            FROM CARI_HESAP_HAREKETLERI
            WHERE cha_kod = '{temiz_kod}'
              AND cha_iptal = 0
              AND cha_d_cins = {DOVIZ_TL}
              AND cha_tarihi >= '{baslangic}'
              AND cha_tarihi <= '{bitis}'
            ORDER BY cha_tarihi ASC, cha_evrakno_sira ASC
        """)

        running = acilis
        hareketler = []
        for h in ham:
            borc = float(h.get("borc") or 0)
            alacak = float(h.get("alacak") or 0)
            running += borc - alacak
            hareketler.append(
                {
                    "tarih": str(h.get("tarih") or "")[:10],
                    "evrak_no": str(h.get("evrak_no") or ""),
                    "aciklama": str(h.get("aciklama") or ""),
                    "borc": borc,
                    "alacak": alacak,
                    "bakiye": running,
                }
            )

        return hareketler, acilis
