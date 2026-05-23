"""
API endpoint testleri — token doğrulama, fatura aktarım, idempotency, rollback.
"""
import json
from decimal import Decimal
from django.test import TestCase, Client
from django.conf import settings

from cari.models import Cari
from fatura.models import Fatura, FaturaKalemi


API_TOKEN = "test-api-token-12345"

SATIN_PAYLOAD = {
    "fat_guid": "abc-guid-001",
    "cari_id": None,  # setUp'ta doldurulur
    "tarih": "2026-01-15",
    "vade_tarihi": "2026-02-15",
    "fatura_no": "API-TEST-0001",
    "aciklama": "Test faturası",
    "satirlar": [
        {"ad": "Hizmet A", "miktar": 2, "birim_fiyat": "500.00", "kdv_orani": 20, "tutar": "1000.00"},
    ],
}


class APITokenDogrulamaTest(TestCase):
    def setUp(self):
        settings.MIKRO_SYNC_API_TOKEN = API_TOKEN
        self.client = Client()

    def test_token_olmadan_401(self):
        resp = self.client.get("/api/v1/ping/")
        self.assertEqual(resp.status_code, 401)

    def test_yanlis_token_401(self):
        resp = self.client.get(
            "/api/v1/ping/",
            HTTP_AUTHORIZATION="Token yanlis-token",
        )
        self.assertEqual(resp.status_code, 401)

    def test_dogru_token_200(self):
        resp = self.client.get(
            "/api/v1/ping/",
            HTTP_AUTHORIZATION=f"Token {API_TOKEN}",
        )
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(data["durum"], "ok")

    def test_token_prefix_olmadan_401(self):
        resp = self.client.get(
            "/api/v1/ping/",
            HTTP_AUTHORIZATION=API_TOKEN,  # "Token " prefix'i yok
        )
        self.assertEqual(resp.status_code, 401)


class CariListesiAPITest(TestCase):
    def setUp(self):
        settings.MIKRO_SYNC_API_TOKEN = API_TOKEN
        self.client = Client()
        Cari.objects.create(ad="Aktif Cari", tip="musteri", aktif=True)
        Cari.objects.create(ad="Pasif Cari", tip="musteri", aktif=False)

    def _get(self, path):
        return self.client.get(path, HTTP_AUTHORIZATION=f"Token {API_TOKEN}")

    def test_sadece_aktif_cariler_gelir(self):
        resp = self._get("/api/v1/cari/")
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        adlar = [c["ad"] for c in data]
        self.assertIn("Aktif Cari", adlar)
        self.assertNotIn("Pasif Cari", adlar)

    def test_cari_alanlar_mevcut(self):
        resp = self._get("/api/v1/cari/")
        data = json.loads(resp.content)
        self.assertTrue(len(data) > 0)
        ilk = data[0]
        for alan in ("id", "ad", "vergi_no", "tip"):
            self.assertIn(alan, ilk)


class FaturaAktarimAPITest(TestCase):
    def setUp(self):
        settings.MIKRO_SYNC_API_TOKEN = API_TOKEN
        self.client = Client()
        self.cari = Cari.objects.create(ad="Test Tedarikçi", tip="tedarikci")

    def _payload(self, **kwargs):
        p = {**SATIN_PAYLOAD, "cari_id": self.cari.pk}
        p.update(kwargs)
        return p

    def _post(self, payload):
        return self.client.post(
            "/api/v1/fatura/aktar/",
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Token {API_TOKEN}",
        )

    def test_basarili_aktarim_fatura_olusturur(self):
        resp = self._post(self._payload())
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(data["durum"], "ok")
        self.assertTrue(Fatura.objects.filter(fatura_no="API-TEST-0001", tip="alis").exists())

    def test_basarili_aktarim_kalemleri_olusturur(self):
        resp = self._post(self._payload())
        fatura_id = json.loads(resp.content)["fatura_id"]
        self.assertEqual(FaturaKalemi.objects.filter(fatura_id=fatura_id).count(), 1)

    def test_tekrar_gonderim_mevcut_doner(self):
        self._post(self._payload())  # birinci
        resp = self._post(self._payload())  # ikinci — aynı fatura_no
        data = json.loads(resp.content)
        self.assertEqual(data["durum"], "mevcut")
        # DB'de hâlâ tek kayıt
        self.assertEqual(
            Fatura.objects.filter(fatura_no="API-TEST-0001", tip="alis").count(), 1
        )

    def test_eksik_zorunlu_alan_400(self):
        payload = self._payload()
        del payload["fatura_no"]
        resp = self._post(payload)
        self.assertEqual(resp.status_code, 400)

    def test_olmayan_cari_404(self):
        resp = self._post(self._payload(cari_id=99999))
        self.assertEqual(resp.status_code, 404)

    def test_gecersiz_json_400(self):
        resp = self.client.post(
            "/api/v1/fatura/aktar/",
            data="bu json degil",
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Token {API_TOKEN}",
        )
        self.assertEqual(resp.status_code, 400)

    def test_token_olmadan_401(self):
        resp = self.client.post(
            "/api/v1/fatura/aktar/",
            data=json.dumps(self._payload()),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 401)

    def test_fatura_alis_olarak_kaydedilir(self):
        self._post(self._payload())
        f = Fatura.objects.get(fatura_no="API-TEST-0001")
        self.assertEqual(f.tip, "alis")
        self.assertEqual(f.cari, self.cari)

    def test_kalem_tutarlari_dogru(self):
        self._post(self._payload())
        f = Fatura.objects.get(fatura_no="API-TEST-0001")
        kalem = f.kalemler.first()
        self.assertEqual(kalem.miktar, Decimal("2"))
        self.assertEqual(kalem.birim_fiyat, Decimal("500.00"))
        self.assertEqual(kalem.kdv_orani, 20)
