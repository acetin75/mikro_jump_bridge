from django.urls import path

from . import views

urlpatterns = [
    path("",                                   views.panel,              name="hy_panel"),
    path("firma-sec/",                         views.firma_sec,          name="hy_firma_sec"),
    path("firma-kartlari/",                    views.firma_kartlari,     name="hy_firma_kartlari"),
    path("firma-kartlari/<str:cari_kod>/",     views.cari_detay,         name="hy_cari_detay"),
    path("hesap-hareketleri/",                 views.hesap_hareketleri,  name="hy_hesap_hareketleri"),
    path("cari-ara/",                          views.cari_ara_api,       name="hy_cari_ara_api"),
    path("bakiye-raporu/",                     views.bakiye_raporu,      name="hy_bakiye_raporu"),
    path("odeme-planlama/",                    views.odeme_planlama,     name="hy_odeme_planlama"),
    path("firma-baglanti-test/",               views.baglanti_test_ajax, name="hy_baglanti_test"),
]
