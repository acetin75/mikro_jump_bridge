"""
Kasa utils testleri — tahsilat, gider ve fatura için otomatik kasa hareketleri.
"""
from decimal import Decimal
import datetime
from django.test import TestCase

from cari.models import Cari
from fatura.models import Fatura
from gider.models import Gider
from kasa.models import KasaHesabi, KasaHareketi
from kasa.utils import (
    tahsilat_kasa_hareketi_olustur,
    gider_kasa_hareketi_olustur,
    fatura_kasa_hareketi_olustur,
)
from tahsilat.models import Tahsilat


def _kasa():
    return KasaHesabi.objects.create(ad="Test Kasa", aktif=True)


def _cari():
    return Cari.objects.create(ad="Test Cari", tip="musteri")


class TahsilatKasaHareketiTest(TestCase):
    def setUp(self):
        self.kasa = _kasa()
        self.cari = _cari()

    def _tahsilat(self, odeme="nakit", tip="tahsilat", tutar="500.00"):
        return Tahsilat.objects.create(
            cari=self.cari,
            tarih=datetime.date.today(),
            tutar=Decimal(tutar),
            tip=tip,
            odeme_yontemi=odeme,
        )

    def test_nakit_tahsilat_kasa_girisi_olusturur(self):
        t = self._tahsilat(odeme="nakit", tip="tahsilat")
        tahsilat_kasa_hareketi_olustur(t)
        hareket = KasaHareketi.objects.get(tahsilat=t)
        self.assertEqual(hareket.tip, "giris")
        self.assertEqual(hareket.tutar, Decimal("500.00"))
        self.assertEqual(hareket.kasa, self.kasa)

    def test_nakit_odeme_kasa_cikisi_olusturur(self):
        t = self._tahsilat(odeme="nakit", tip="odeme")
        tahsilat_kasa_hareketi_olustur(t)
        hareket = KasaHareketi.objects.get(tahsilat=t)
        self.assertEqual(hareket.tip, "cikis")

    def test_havale_ile_kasa_hareketi_olusturmaz(self):
        t = self._tahsilat(odeme="havale")
        tahsilat_kasa_hareketi_olustur(t)
        self.assertFalse(KasaHareketi.objects.filter(tahsilat=t).exists())

    def test_tekrar_cagirma_mukerrer_olusturmaz(self):
        t = self._tahsilat(odeme="nakit")
        tahsilat_kasa_hareketi_olustur(t)
        tahsilat_kasa_hareketi_olustur(t)  # ikinci çağrı
        self.assertEqual(KasaHareketi.objects.filter(tahsilat=t).count(), 1)

    def test_aktif_kasa_yoksa_hareket_olusturmaz(self):
        self.kasa.aktif = False
        self.kasa.save()
        t = self._tahsilat(odeme="nakit")
        tahsilat_kasa_hareketi_olustur(t)  # sessizce atlamalı
        self.assertFalse(KasaHareketi.objects.filter(tahsilat=t).exists())


class GiderKasaHareketiTest(TestCase):
    def setUp(self):
        self.kasa = _kasa()

    def _gider(self, odeme="nakit", kdv_haric="1000.00", kdv_orani=20):
        return Gider.objects.create(
            tarih=datetime.date.today(),
            aciklama="Test Gider",
            kdv_haric_tutar=Decimal(kdv_haric),
            kdv_orani=kdv_orani,
            odeme_yontemi=odeme,
        )

    def test_nakit_gider_kasa_cikisi_olusturur(self):
        g = self._gider(odeme="nakit")
        gider_kasa_hareketi_olustur(g)
        hareket = KasaHareketi.objects.get(gider=g)
        self.assertEqual(hareket.tip, "cikis")
        # 1000 + %20 KDV = 1200
        self.assertEqual(hareket.tutar, Decimal("1200.00"))

    def test_banka_ile_kasa_hareketi_olusturmaz(self):
        g = self._gider(odeme="banka")
        gider_kasa_hareketi_olustur(g)
        self.assertFalse(KasaHareketi.objects.filter(gider=g).exists())

    def test_sifir_kdv_tutari_dogru(self):
        g = self._gider(odeme="nakit", kdv_haric="500.00", kdv_orani=0)
        gider_kasa_hareketi_olustur(g)
        hareket = KasaHareketi.objects.get(gider=g)
        self.assertEqual(hareket.tutar, Decimal("500.00"))


class FaturaKasaHareketiTest(TestCase):
    def setUp(self):
        self.kasa = _kasa()
        self.cari = _cari()

    def _fatura(self, odeme="nakit", tip="satis", durum="odendi"):
        from fatura.models import FaturaKalemi
        import datetime
        f = Fatura.objects.create(
            cari=self.cari,
            tip=tip,
            durum=durum,
            tarih=datetime.date.today(),
            fatura_no=f"TST-{Fatura.objects.count() + 1:04d}",
            odeme_yontemi=odeme,
        )
        FaturaKalemi.objects.create(
            fatura=f,
            aciklama="Test",
            miktar=Decimal("1"),
            birim_fiyat=Decimal("1000.00"),
            kdv_orani=20,
        )
        return f

    def test_nakit_odendi_satis_kasa_girisi(self):
        f = self._fatura(odeme="nakit", tip="satis", durum="odendi")
        fatura_kasa_hareketi_olustur(f)
        hareketler = KasaHareketi.objects.filter(fatura=f)
        self.assertEqual(hareketler.count(), 1)
        self.assertEqual(hareketler.first().tip, "giris")

    def test_nakit_odendi_alis_kasa_cikisi(self):
        f = self._fatura(odeme="nakit", tip="alis", durum="odendi")
        fatura_kasa_hareketi_olustur(f)
        hareketler = KasaHareketi.objects.filter(fatura=f)
        self.assertEqual(hareketler.count(), 1)
        self.assertEqual(hareketler.first().tip, "cikis")

    def test_havale_ile_kasa_hareketi_olusturmaz(self):
        f = self._fatura(odeme="havale", durum="odendi")
        fatura_kasa_hareketi_olustur(f)
        self.assertFalse(KasaHareketi.objects.filter(fatura=f).exists())

    def test_odenmemis_fatura_kasa_hareketi_olusturmaz(self):
        f = self._fatura(odeme="nakit", durum="kesildi")
        fatura_kasa_hareketi_olustur(f)
        self.assertFalse(KasaHareketi.objects.filter(fatura=f).exists())
