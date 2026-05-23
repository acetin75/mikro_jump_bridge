"""
Fatura model testleri — KDV hesapları, toplam, vade ve durum özellikleri.
"""
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone

from cari.models import Cari
from fatura.models import Fatura, FaturaKalemi


def _cari(ad="Test Cari"):
    return Cari.objects.create(ad=ad, tip="musteri")


def _fatura(cari=None, tip="satis", durum="kesildi", vade=None):
    return Fatura.objects.create(
        cari=cari or _cari(),
        tip=tip,
        durum=durum,
        tarih=timezone.now().date(),
        vade_tarihi=vade,
        fatura_no=f"TST-{Fatura.objects.count() + 1:04d}",
    )


def _kalem(fatura, miktar="2", birim_fiyat="100.00", kdv_orani=20):
    return FaturaKalemi.objects.create(
        fatura=fatura,
        aciklama="Test Kalem",
        miktar=Decimal(miktar),
        birim_fiyat=Decimal(birim_fiyat),
        kdv_orani=kdv_orani,
    )


class FaturaKdvHesaplariTest(TestCase):
    """KDV ve tutar property'lerinin doğruluğu."""

    def setUp(self):
        self.fatura = _fatura()

    def test_kdv_haric_toplam_tek_kalem(self):
        _kalem(self.fatura, miktar="1", birim_fiyat="1000.00", kdv_orani=20)
        self.assertEqual(self.fatura.kdv_haric_toplam, Decimal("1000.00"))

    def test_kdv_toplam_yuzde_20(self):
        _kalem(self.fatura, miktar="1", birim_fiyat="1000.00", kdv_orani=20)
        self.assertEqual(self.fatura.kdv_toplam, Decimal("200.00"))

    def test_genel_toplam_kdv_dahil(self):
        _kalem(self.fatura, miktar="1", birim_fiyat="1000.00", kdv_orani=20)
        self.assertEqual(self.fatura.genel_toplam, Decimal("1200.00"))

    def test_miktar_carpimi_dogru(self):
        # 3 adet × 500 ₺ = 1500 ₺ KDV hariç
        _kalem(self.fatura, miktar="3", birim_fiyat="500.00", kdv_orani=10)
        self.assertEqual(self.fatura.kdv_haric_toplam, Decimal("1500.00"))
        self.assertEqual(self.fatura.kdv_toplam, Decimal("150.00"))
        self.assertEqual(self.fatura.genel_toplam, Decimal("1650.00"))

    def test_sifir_kdv_orani(self):
        _kalem(self.fatura, miktar="1", birim_fiyat="500.00", kdv_orani=0)
        self.assertEqual(self.fatura.kdv_toplam, Decimal("0.00"))
        self.assertEqual(self.fatura.genel_toplam, Decimal("500.00"))

    def test_coklu_kalem_toplami(self):
        _kalem(self.fatura, miktar="1", birim_fiyat="100.00", kdv_orani=20)
        _kalem(self.fatura, miktar="2", birim_fiyat="200.00", kdv_orani=10)
        # KDV hariç: 100 + 400 = 500
        self.assertEqual(self.fatura.kdv_haric_toplam, Decimal("500.00"))
        # KDV: 20 + 40 = 60
        self.assertEqual(self.fatura.kdv_toplam, Decimal("60.00"))
        # Genel: 120 + 440 = 560
        self.assertEqual(self.fatura.genel_toplam, Decimal("560.00"))

    def test_kalemsiz_fatura_sifir_doner(self):
        self.assertEqual(self.fatura.kdv_haric_toplam, Decimal("0"))
        self.assertEqual(self.fatura.kdv_toplam, Decimal("0"))
        self.assertEqual(self.fatura.genel_toplam, Decimal("0"))

    def test_kdv_ozeti_gruplama(self):
        _kalem(self.fatura, miktar="1", birim_fiyat="100.00", kdv_orani=20)
        _kalem(self.fatura, miktar="1", birim_fiyat="200.00", kdv_orani=10)
        ozet = self.fatura.kdv_ozeti
        self.assertIn(20, ozet)
        self.assertIn(10, ozet)
        self.assertEqual(ozet[20]["matrah"], Decimal("100.00"))
        self.assertEqual(ozet[20]["kdv"], Decimal("20.00"))
        self.assertEqual(ozet[10]["matrah"], Decimal("200.00"))
        self.assertEqual(ozet[10]["kdv"], Decimal("20.00"))

    def test_kdv_ozeti_sirali_doner(self):
        _kalem(self.fatura, miktar="1", birim_fiyat="100.00", kdv_orani=20)
        _kalem(self.fatura, miktar="1", birim_fiyat="100.00", kdv_orani=8)
        oranlar = list(self.fatura.kdv_ozeti.keys())
        self.assertEqual(oranlar, sorted(oranlar))


class FaturaVadeTarihi(TestCase):
    """vadesi_gecti_mi property'si."""

    def test_vadesi_gecmis_kesildi_fatura(self):
        gecmis = timezone.now().date().replace(year=2020)
        f = _fatura(durum="kesildi", vade=gecmis)
        self.assertTrue(f.vadesi_gecti_mi)

    def test_vadesi_gecmemis(self):
        gelecek = timezone.now().date().replace(year=2099)
        f = _fatura(durum="kesildi", vade=gelecek)
        self.assertFalse(f.vadesi_gecti_mi)

    def test_odendi_durumunda_vade_gecmez(self):
        gecmis = timezone.now().date().replace(year=2020)
        f = _fatura(durum="odendi", vade=gecmis)
        self.assertFalse(f.vadesi_gecti_mi)

    def test_iptal_durumunda_vade_gecmez(self):
        gecmis = timezone.now().date().replace(year=2020)
        f = _fatura(durum="iptal", vade=gecmis)
        self.assertFalse(f.vadesi_gecti_mi)

    def test_vade_tarihi_yok(self):
        f = _fatura(durum="kesildi", vade=None)
        self.assertFalse(f.vadesi_gecti_mi)


class FaturaNoUretimTest(TestCase):
    """Fatura no otomatik üretimi."""

    def test_satis_no_prefix_sat(self):
        f = Fatura.objects.create(
            cari=_cari(), tip="satis", durum="taslak",
            tarih=timezone.now().date(),
        )
        self.assertTrue(f.fatura_no.startswith("SAT-"))

    def test_alis_no_prefix_ali(self):
        f = Fatura.objects.create(
            cari=_cari(), tip="alis", durum="taslak",
            tarih=timezone.now().date(),
        )
        self.assertTrue(f.fatura_no.startswith("ALI-"))

    def test_manuel_no_korunur(self):
        f = Fatura.objects.create(
            cari=_cari(), tip="satis", durum="taslak",
            tarih=timezone.now().date(), fatura_no="OZEL-001",
        )
        self.assertEqual(f.fatura_no, "OZEL-001")
