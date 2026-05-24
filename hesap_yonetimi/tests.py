"""hesap_yonetimi acik redirect koruma testleri."""

from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
from django.urls import reverse

from hesap_yonetimi.views import _guvenli_next
from sync_motor.models import FirmaAyar


class GuvenliNextTestleri(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_dis_host_reddedilir(self):
        req = self.factory.get("/")
        sonuc = _guvenli_next(req, "http://kotu.example.com/calar")
        self.assertNotIn("kotu.example.com", sonuc)

    def test_protocol_relative_reddedilir(self):
        req = self.factory.get("/")
        sonuc = _guvenli_next(req, "//kotu.example.com/calar")
        self.assertNotIn("kotu.example.com", sonuc)

    def test_yerel_path_kabul(self):
        req = self.factory.get("/")
        sonuc = _guvenli_next(req, "/hesap/")
        self.assertEqual(sonuc, "/hesap/")

    def test_bos_varsayilan(self):
        req = self.factory.get("/")
        sonuc = _guvenli_next(req, None)
        self.assertTrue(sonuc.startswith("/"))


class FirmaSecOpenRedirectTestleri(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("u", password="p123!xy.")
        self.client.login(username="u", password="p123!xy.")
        self.firma = FirmaAyar.objects.create(
            ad="A",
            mikro_sunucu="10.0.0.1",
            mikro_port=8094,
            mikro_kullanici="SRV",
            firma_kodu="A1",
            calisma_yili="2026",
            aktif=True,
        )

    def test_post_dis_host_next_yonlendirilmez(self):
        yanit = self.client.post(
            reverse("hy_firma_sec"),
            {
                "firma_id": self.firma.pk,
                "baglanti_modu": "yerel",
                "next": "http://kotu.example.com/calar",
            },
        )
        self.assertEqual(yanit.status_code, 302)
        self.assertNotIn("kotu.example.com", yanit["Location"])
