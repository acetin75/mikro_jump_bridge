"""
MikroApiClient ve sql_utils testleri — ağ çağrıları mock'lanır.
"""

import hashlib
from datetime import date
from unittest.mock import patch

import requests
from django.test import TestCase

from sync_motor.client import MikroApiClient, MikroApiHatasi
from sync_motor.models import FirmaAyar
from sync_motor.sql_utils import sql_date, sql_int, sql_like, sql_str, whitelist

# ---------------------------------------------------------------------------
# sql_utils
# ---------------------------------------------------------------------------


class SqlUtilsTestleri(TestCase):
    def test_sql_str_temel(self):
        self.assertEqual(sql_str("abc"), "'abc'")

    def test_sql_str_tek_tirnak_kacar(self):
        self.assertEqual(sql_str("O'Brien"), "'O''Brien'")

    def test_sql_str_none_null_doner(self):
        self.assertEqual(sql_str(None), "NULL")

    def test_sql_str_nul_byte_temizler(self):
        self.assertNotIn("\x00", sql_str("a\x00b"))

    def test_sql_str_uzun_kirpilir(self):
        s = sql_str("x" * 1000, maks_uzunluk=10)
        self.assertEqual(s, "'" + "x" * 10 + "'")

    def test_sql_like_yuzde_kacar(self):
        s = sql_like("50%")
        self.assertIn("\\%", s)
        self.assertTrue(s.startswith("'%"))
        self.assertTrue(s.endswith("%'"))

    def test_sql_int_dogru(self):
        self.assertEqual(sql_int("42"), 42)
        self.assertEqual(sql_int("abc", varsayilan=7), 7)

    def test_sql_date_date_objesi(self):
        self.assertEqual(sql_date(date(2026, 5, 24)), "'2026-05-24'")

    def test_sql_date_str_yyyymmdd(self):
        self.assertEqual(sql_date("2026-05-24"), "'2026-05-24'")

    def test_sql_date_gecersiz_format_hata_firlatir(self):
        with self.assertRaises(ValueError):
            sql_date("24/05/2026")

    def test_whitelist_izinli_anahtar(self):
        izinli = {"desc": "x DESC", "asc": "x ASC"}
        self.assertEqual(whitelist("desc", izinli, "asc"), "x DESC")

    def test_whitelist_yabanci_anahtar_varsayilana_duser(self):
        izinli = {"desc": "x DESC", "asc": "x ASC"}
        self.assertEqual(whitelist("DROP TABLE", izinli, "asc"), "x ASC")


# ---------------------------------------------------------------------------
# MikroApiClient — auth ve davranış
# ---------------------------------------------------------------------------


class MikroApiClientTestleri(TestCase):
    def setUp(self):
        self.firma = FirmaAyar.objects.create(
            ad="X",
            mikro_sunucu="10.0.0.1",
            mikro_port=8094,
            mikro_kullanici="SRV",
            firma_kodu="X1",
            calisma_yili="2026",
        )
        self.firma.sifre_kaydet("gizli")
        self.firma.save()

    def test_sifre_hash_md5_format(self):
        c = MikroApiClient(self.firma)
        h = c._sifre_hash()
        # MD5 hex 32 karakter
        self.assertEqual(len(h), 32)
        bugun = date.today().strftime("%Y-%m-%d")
        beklenen = hashlib.md5(f"{bugun} gizli".encode()).hexdigest()
        self.assertEqual(h, beklenen)

    def test_mikro_obj_alanlari(self):
        c = MikroApiClient(self.firma)
        obj = c._mikro_obj()
        self.assertEqual(obj["FirmaKodu"], "X1")
        self.assertEqual(obj["KullaniciKodu"], "SRV")
        self.assertEqual(len(obj["Sifre"]), 32)
        self.assertEqual(obj["CalismaYili"], "2026")

    def test_post_connection_error_apihatasi(self):
        c = MikroApiClient(self.firma)
        with patch(
            "sync_motor.client.requests.post",
            side_effect=requests.exceptions.ConnectionError("conn"),
        ):
            with self.assertRaises(MikroApiHatasi):
                c._post("Bir", {})

    def test_post_timeout_apihatasi(self):
        c = MikroApiClient(self.firma)
        with patch("sync_motor.client.requests.post", side_effect=requests.exceptions.Timeout()):
            with self.assertRaises(MikroApiHatasi):
                c._post("Bir", {})

    def test_post_gecersiz_json_apihatasi(self):
        c = MikroApiClient(self.firma)

        class Resp:
            status_code = 200

            def raise_for_status(self):
                return None

            def json(self):
                raise ValueError("not json")

        with patch("sync_motor.client.requests.post", return_value=Resp()):
            with self.assertRaises(MikroApiHatasi):
                c._post("Bir", {})

    def test_post_hata_anahtari_apihatasi(self):
        c = MikroApiClient(self.firma)

        class Resp:
            status_code = 200

            def raise_for_status(self):
                return None

            def json(self):
                return {"Hata": "Yetkisiz"}

        with patch("sync_motor.client.requests.post", return_value=Resp()):
            with self.assertRaises(MikroApiHatasi):
                c._post("Bir", {})

    def test_extract_list_response_liste(self):
        self.assertEqual(MikroApiClient._extract_list_response([1, 2], "X"), [1, 2])

    def test_extract_list_response_tercih_anahtari(self):
        sonuc = {"Data": [{"a": 1}]}
        self.assertEqual(MikroApiClient._extract_list_response(sonuc, "X"), [{"a": 1}])

    def test_extract_list_response_fallback_ilk_list(self):
        sonuc = {"sarmal": [{"a": 1}], "meta": "x"}
        self.assertEqual(MikroApiClient._extract_list_response(sonuc, "X"), [{"a": 1}])

    def test_extract_list_response_bos(self):
        self.assertEqual(MikroApiClient._extract_list_response({"meta": "x"}, "X"), [])

    def test_sql_oku_basarili_parse(self):
        c = MikroApiClient(self.firma)
        yanit = {"result": [{"StatusCode": 200, "Data": [{"SQLResult1": [{"k": 1}]}]}]}
        with patch.object(c, "_post", return_value=yanit):
            self.assertEqual(c.sql_oku("SELECT 1"), [{"k": 1}])

    def test_sql_oku_hata_durumu_bos_doner(self):
        c = MikroApiClient(self.firma)
        yanit = {"result": [{"IsError": True, "StatusCode": 500, "ErrorMessage": "bozuk"}]}
        with patch.object(c, "_post", return_value=yanit):
            self.assertEqual(c.sql_oku("SELECT 1"), [])

    def test_baglanti_test_basarili(self):
        c = MikroApiClient(self.firma)

        class Resp:
            def raise_for_status(self):
                return None

        with patch("sync_motor.client.requests.get", return_value=Resp()):
            sonuc = c.baglanti_test()
        self.assertTrue(sonuc["basarili"])

    def test_baglanti_test_baglanti_hatasi(self):
        c = MikroApiClient(self.firma)
        with patch(
            "sync_motor.client.requests.get",
            side_effect=requests.exceptions.ConnectionError("nope"),
        ):
            sonuc = c.baglanti_test()
        self.assertFalse(sonuc["basarili"])
