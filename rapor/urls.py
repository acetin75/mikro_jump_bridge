from django.urls import path
from . import views

app_name = "rapor"

urlpatterns = [
    path("", views.rapor_index, name="index"),
    path("donemsel/", views.donemsel_ozet, name="donemsel"),
    path("excel/cari-bakiye/", views.excel_cari_bakiye, name="excel_cari_bakiye"),
    path("excel/cari-ekstre/", views.excel_cari_ekstre, name="excel_cari_ekstre"),
    path("excel/tahsilat/", views.excel_tahsilat, name="excel_tahsilat"),
    path("excel/gider/", views.excel_gider, name="excel_gider"),
    path("excel/kdv-beyanname/", views.excel_kdv_beyanname, name="excel_kdv_beyanname"),
]
