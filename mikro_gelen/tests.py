"""
mikro_gelen test paketi.

Kapsam:
  - MikroFatura model davranışları
  - ham_veri property
  - fat_guid unique kısıtı
"""
import json

from django.test import TestCase

from sync_motor.models import FirmaAyar
from .models import MikroFatura


class MikroFaturaTestleri(TestCase):

    def setUp(self):
        self.firma = FirmaAyar.objects.create(ad="Test Firma")
        self.ham = {"fat_Guid": "abc-123", "fat_cari_kod": "C001", "fat_toplam": "1000.00"}
        self.fatura = MikroFatura.objects.create(
            firma_ayar=self.firma,
            fat_guid="abc-123",
            fat_cari_kod="C001",
            ham_json=json.dumps(self.ham, ensure_ascii=False),
        )

    def test_ham_veri_dict_doner(self):
        veri = self.fatura.ham_veri
        self.assertIsInstance(veri, dict)
        self.assertEqual(veri["fat_cari_kod"], "C001")

    def test_bos_ham_json_bos_dict_doner(self):
        self.fatura.ham_json = ""
        self.assertEqual(self.fatura.ham_veri, {})

    def test_fat_guid_unique(self):
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            MikroFatura.objects.create(
                firma_ayar=self.firma,
                fat_guid="abc-123",  # aynı GUID
            )

    def test_varsayilan_durum_ham(self):
        self.assertEqual(self.fatura.durum, "ham")
