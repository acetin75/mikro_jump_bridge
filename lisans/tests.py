"""Lisans uygulamasi testleri — anahtar uretme/dogrulama + middleware davranisi."""

from datetime import date, timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from lisans.models import LisansBilgisi
from lisans.utils import lisans_al, lisans_anahtari_dogrula, lisans_anahtari_uret


class LisansAnahtariTestleri(TestCase):
    def test_uret_dogrula_basarili(self):
        bitis = (date.today() + timedelta(days=30)).isoformat()
        anahtar = lisans_anahtari_uret("MUST001", bitis, tip="premium")
        sonuc = lisans_anahtari_dogrula(anahtar)
        self.assertIsNotNone(sonuc)
        self.assertEqual(sonuc["musteri"], "MUST001")
        self.assertEqual(sonuc["tip"], "premium")

    def test_dogrula_bozuk_anahtar_none(self):
        self.assertIsNone(lisans_anahtari_dogrula("AAAA"))

    def test_dogrula_imza_bozuk_none(self):
        bitis = (date.today() + timedelta(days=30)).isoformat()
        anahtar = lisans_anahtari_uret("M1", bitis)
        # son karakteri bozarak imzayi gecersiz yap
        import base64

        ham = base64.urlsafe_b64decode(anahtar.encode()).decode()
        bozuk = ham[:-1] + ("0" if ham[-1] != "0" else "1")
        bozuk_anahtar = base64.urlsafe_b64encode(bozuk.encode()).decode()
        self.assertIsNone(lisans_anahtari_dogrula(bozuk_anahtar))

    def test_dogrula_suresi_gecmis_none(self):
        bitis = (date.today() - timedelta(days=1)).isoformat()
        anahtar = lisans_anahtari_uret("M1", bitis)
        self.assertIsNone(lisans_anahtari_dogrula(anahtar))


class LisansAlSingletonTestleri(TestCase):
    def test_yoksa_olusturur(self):
        self.assertEqual(LisansBilgisi.objects.count(), 0)
        lisans = lisans_al()
        self.assertEqual(LisansBilgisi.objects.count(), 1)
        self.assertIsNotNone(lisans.pk)

    def test_varsa_ayni_kaydi_doner(self):
        l1 = lisans_al()
        l2 = lisans_al()
        self.assertEqual(l1.pk, l2.pk)


class LisansMiddlewareTestleri(TestCase):
    """Süresi dolmuş lisansta /lisans/bitti/ yönlendirmesi yapilmali."""

    def setUp(self):
        self.user = User.objects.create_user("u", password="p123!xy.")
        self.client.login(username="u", password="p123!xy.")

    def test_gecerli_lisansta_yonlendirme_yok(self):
        # Yeni kayit → varsayilan deneme süresi (15 gün) gecerli
        lisans_al()
        with patch("lisans.utils.lisans_al") as m:
            m.return_value.gecerli_mi = True
            yanit = self.client.get("/", follow=False)
        # Login zorunlu zaten karsilandi; lisans muaf değil → middleware geçirmeli
        # 200 veya 302 (anasayfa redirect'i) olabilir, /lisans/bitti/ olmamali
        self.assertNotIn("/lisans/bitti/", yanit.get("Location", ""))

    def test_lisans_url_lere_erisim_muaf(self):
        # Lisans bitmiş bile olsa /lisans/ erişilebilir olmalı
        lisans = lisans_al()
        lisans.install_tarihi = date.today() - timedelta(days=30)
        lisans.save()
        yanit = self.client.get(reverse("lisans_durum"))
        self.assertEqual(yanit.status_code, 200)
