"""
Yetki sistemi testleri — yonetici_mi, muhasebeci_mi, dekoratörler, YetkiMiddleware.
"""
from django.contrib.auth.models import Group, User
from django.test import TestCase, RequestFactory
from django.contrib.messages.storage.fallback import FallbackStorage

from muhasebe_buro.permissions import (
    yonetici_mi,
    muhasebeci_mi,
    rol_adi,
    yonetici_gerekli,
    muhasebeci_gerekli,
)


def _gruplari_olustur():
    for isim in ["Yönetici", "Muhasebeci", "Görüntüleyici"]:
        Group.objects.get_or_create(name=isim)


def _kullanici(username, grup=None, superuser=False, staff=False):
    u = User.objects.create_user(username=username, password="test1234!")
    u.is_superuser = superuser
    u.is_staff = staff
    u.save()
    if grup:
        grp, _ = Group.objects.get_or_create(name=grup)
        u.groups.add(grp)
    return u


class YoneticiMiTest(TestCase):
    def setUp(self):
        _gruplari_olustur()

    def test_superuser_yoneticidir(self):
        u = _kullanici("su", superuser=True)
        self.assertTrue(yonetici_mi(u))

    def test_staff_yoneticidir(self):
        u = _kullanici("st", staff=True)
        self.assertTrue(yonetici_mi(u))

    def test_yonetici_grubundaki_yoneticidir(self):
        u = _kullanici("y1", grup="Yönetici")
        self.assertTrue(yonetici_mi(u))

    def test_muhasebeci_yonetici_degildir(self):
        u = _kullanici("m1", grup="Muhasebeci")
        self.assertFalse(yonetici_mi(u))

    def test_goruntuleyici_yonetici_degildir(self):
        u = _kullanici("g1", grup="Görüntüleyici")
        self.assertFalse(yonetici_mi(u))

    def test_grupsuz_kullanici_yonetici_degildir(self):
        u = _kullanici("n1")
        self.assertFalse(yonetici_mi(u))


class MuhasebeciMiTest(TestCase):
    def setUp(self):
        _gruplari_olustur()

    def test_yonetici_muhasebeci_sayilir(self):
        u = _kullanici("y2", grup="Yönetici")
        self.assertTrue(muhasebeci_mi(u))

    def test_muhasebeci_muhasebeci_sayilir(self):
        u = _kullanici("m2", grup="Muhasebeci")
        self.assertTrue(muhasebeci_mi(u))

    def test_goruntuleyici_muhasebeci_sayilmaz(self):
        u = _kullanici("g2", grup="Görüntüleyici")
        self.assertFalse(muhasebeci_mi(u))

    def test_superuser_muhasebeci_sayilir(self):
        u = _kullanici("su2", superuser=True)
        self.assertTrue(muhasebeci_mi(u))


class RolAdiTest(TestCase):
    def setUp(self):
        _gruplari_olustur()

    def test_superuser_rol_adi(self):
        u = _kullanici("su3", superuser=True)
        self.assertEqual(rol_adi(u), "Süper Yönetici")

    def test_muhasebeci_rol_adi(self):
        u = _kullanici("m3", grup="Muhasebeci")
        self.assertEqual(rol_adi(u), "Muhasebeci")

    def test_grupsuz_goruntuleyici_varsayilan(self):
        u = _kullanici("n2")
        self.assertEqual(rol_adi(u), "Görüntüleyici")


def _request_olustur(factory, user, path="/test/ekle/"):
    """Mesaj desteğiyle request üret."""
    req = factory.get(path)
    req.user = user
    req.session = {}
    messages_storage = FallbackStorage(req)
    req._messages = messages_storage
    return req


class YoneticiGerekliDekoratorTest(TestCase):
    def setUp(self):
        _gruplari_olustur()
        self.factory = RequestFactory()

    def _dummy_view(self, request):
        from django.http import HttpResponse
        return HttpResponse("ok")

    def test_yonetici_erisebilir(self):
        u = _kullanici("yd1", grup="Yönetici")
        req = _request_olustur(self.factory, u)
        view = yonetici_gerekli(self._dummy_view)
        resp = view(req)
        self.assertEqual(resp.status_code, 200)

    def test_muhasebeci_erisemez(self):
        u = _kullanici("yd2", grup="Muhasebeci")
        req = _request_olustur(self.factory, u)
        view = yonetici_gerekli(self._dummy_view)
        resp = view(req)
        self.assertEqual(resp.status_code, 302)

    def test_superuser_erisebilir(self):
        u = _kullanici("yd3", superuser=True)
        req = _request_olustur(self.factory, u)
        view = yonetici_gerekli(self._dummy_view)
        resp = view(req)
        self.assertEqual(resp.status_code, 200)


class MuhasebeciGerekliDekoratorTest(TestCase):
    def setUp(self):
        _gruplari_olustur()
        self.factory = RequestFactory()

    def _dummy_view(self, request):
        from django.http import HttpResponse
        return HttpResponse("ok")

    def test_muhasebeci_erisebilir(self):
        u = _kullanici("md1", grup="Muhasebeci")
        req = _request_olustur(self.factory, u)
        view = muhasebeci_gerekli(self._dummy_view)
        resp = view(req)
        self.assertEqual(resp.status_code, 200)

    def test_yonetici_erisebilir(self):
        u = _kullanici("md2", grup="Yönetici")
        req = _request_olustur(self.factory, u)
        view = muhasebeci_gerekli(self._dummy_view)
        resp = view(req)
        self.assertEqual(resp.status_code, 200)

    def test_goruntuleyici_erisemez(self):
        u = _kullanici("md3", grup="Görüntüleyici")
        req = _request_olustur(self.factory, u)
        view = muhasebeci_gerekli(self._dummy_view)
        resp = view(req)
        self.assertEqual(resp.status_code, 302)
