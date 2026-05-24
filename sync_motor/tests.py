"""
sync_motor test paketi.

Kapsam:
  - FirmaAyar model davranışları (şifre güvenliği)
  - ImportLog property'leri
  - View erişim kontrolü (login zorunluluğu)
  - View POST akışları (PRG pattern)
"""
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import FirmaAyar, ImportLog

# ---------------------------------------------------------------------------
# Model testleri
# ---------------------------------------------------------------------------

class FirmaAyarSifreTestleri(TestCase):
    """Şifre kaydet/al döngüsü ve güvenlik."""

    def setUp(self):
        self.firma = FirmaAyar.objects.create(
            ad="Test Firma",
            mikro_sunucu="192.168.1.10",
            mikro_port=8094,
            mikro_kullanici="admin",
            firma_kodu="TEST",
            calisma_yili="2026",
        )

    def test_sifre_kaydet_ve_al(self):
        self.firma.sifre_kaydet("gizli123")
        self.firma.save()
        self.assertEqual(self.firma.sifre_al(), "gizli123")

    def test_ham_sifre_db_ye_yazilmaz(self):
        self.firma.sifre_kaydet("gizli123")
        self.firma.save()
        self.assertNotEqual(self.firma._mikro_sifre_sifreli, "gizli123")

    def test_bos_sifre_bos_string_doner(self):
        self.assertEqual(self.firma.sifre_al(), "")

    def test_api_url_ozellik(self):
        self.assertEqual(
            self.firma.api_url,
            "http://192.168.1.10:8094/Api/APIMethods",
        )


class ImportLogTestleri(TestCase):
    """ImportLog property ve durum testleri."""

    def setUp(self):
        self.firma = FirmaAyar.objects.create(ad="Test Firma")
        self.log = ImportLog.objects.create(
            firma_ayar=self.firma,
            durum="tamamlandi",
            cekilen_adet=10,
            aktarilan_adet=8,
            hata_adet=2,
        )

    def test_basari_yuzdesi_hesabi(self):
        self.assertEqual(self.log.basari_yuzdesi, 80.0)

    def test_basari_yuzdesi_sifir_cekilen(self):
        self.log.cekilen_adet = 0
        self.assertEqual(self.log.basari_yuzdesi, 0.0)


# ---------------------------------------------------------------------------
# View testleri — erişim kontrolü
# ---------------------------------------------------------------------------

class ViewErisimTestleri(TestCase):
    """Login zorunluluğu: oturum açmadan erişim /giris/'e yönlendirmeli."""

    def test_anasayfa_login_gerektirir(self):
        yanit = self.client.get(reverse("anasayfa"))
        self.assertRedirects(yanit, "/giris/?next=/", fetch_redirect_response=False)

    def test_firma_liste_login_gerektirir(self):
        yanit = self.client.get(reverse("firma_liste"))
        self.assertIn("/giris/", yanit["Location"])

    def test_import_liste_login_gerektirir(self):
        yanit = self.client.get(reverse("import_liste"))
        self.assertIn("/giris/", yanit["Location"])


class FirmaEklemeViewTestleri(TestCase):
    """Firma ekleme POST akışı (PRG pattern)."""

    def setUp(self):
        self.user = User.objects.create_user("testuser", password="sifre123!")
        self.client.login(username="testuser", password="sifre123!")

    def test_firma_ekle_get(self):
        yanit = self.client.get(reverse("firma_ekle"))
        self.assertEqual(yanit.status_code, 200)

    def test_firma_ekle_post_basarili_redirect(self):
        yanit = self.client.post(reverse("firma_ekle"), {
            "ad": "Yeni Firma",
            "baglanti_tipi": "api",
            "mikro_sunucu": "192.168.1.5",
            "mikro_port": 8094,
            "mikro_kullanici": "admin",
            "firma_kodu": "YNF",
            "calisma_yili": "2026",
        })
        self.assertRedirects(yanit, reverse("firma_liste"), fetch_redirect_response=False)
        self.assertTrue(FirmaAyar.objects.filter(ad="Yeni Firma").exists())

    def test_firma_ekle_post_eksik_alan_form_tekrar_gosterir(self):
        yanit = self.client.post(reverse("firma_ekle"), {"ad": ""})
        self.assertEqual(yanit.status_code, 200)
