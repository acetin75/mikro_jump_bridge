"""Posta uygulamasi testleri."""

from django.test import TestCase

from posta.forms import MailAyarForm
from posta.models import MailAyar


class MailAyarSingletonTestleri(TestCase):
    def test_save_aktif_yapinca_digerleri_pasiflesir(self):
        a1 = MailAyar.objects.create(
            smtp_sunucu="mail.example.com",
            smtp_port=587,
            kullanici="a@example.com",
            aktif=True,
        )
        a2 = MailAyar.objects.create(
            smtp_sunucu="mail2.example.com",
            smtp_port=587,
            kullanici="b@example.com",
            aktif=True,
        )
        a1.refresh_from_db()
        self.assertFalse(a1.aktif)
        self.assertTrue(a2.aktif)

    def test_pasif_kayit_digerlerini_etkilemez(self):
        a1 = MailAyar.objects.create(
            smtp_sunucu="mail.example.com",
            smtp_port=587,
            kullanici="a@example.com",
            aktif=True,
        )
        MailAyar.objects.create(
            smtp_sunucu="mail2.example.com",
            smtp_port=587,
            kullanici="b@example.com",
            aktif=False,
        )
        a1.refresh_from_db()
        self.assertTrue(a1.aktif)


class MailAyarFormTestleri(TestCase):
    BASE_DATA = {
        "smtp_sunucu": "mail.example.com",
        "smtp_port": 587,
        "kullanici": "a@example.com",
        "tls_kullan": True,
        "tls_dogrulamayi_atla": False,
        "gonderen_ad": "Test",
        "gonderen_email": "a@example.com",
        "aktif": True,
    }

    def test_ilk_kayit_sifresiz_gecersiz(self):
        form = MailAyarForm(data={**self.BASE_DATA, "sifre": ""})
        self.assertFalse(form.is_valid())
        self.assertIn("sifre", form.errors)

    def test_ilk_kayit_sifre_ile_gecerli(self):
        form = MailAyarForm(data={**self.BASE_DATA, "sifre": "geçerli123"})
        self.assertTrue(form.is_valid(), form.errors)
        ayar = form.save()
        self.assertNotEqual(ayar._sifre_sifreli, "")
        self.assertEqual(ayar.sifre_al(), "geçerli123")

    def test_duzenleme_bos_sifre_mevcut_korunur(self):
        ayar = MailAyar.objects.create(
            smtp_sunucu="mail.example.com",
            smtp_port=587,
            kullanici="a@example.com",
        )
        ayar.sifre_kaydet("eski")
        ayar.save()

        form = MailAyarForm(data={**self.BASE_DATA, "sifre": ""}, instance=ayar)
        self.assertTrue(form.is_valid(), form.errors)
        guncel = form.save()
        self.assertEqual(guncel.sifre_al(), "eski")
