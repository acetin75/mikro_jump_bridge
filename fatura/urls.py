from django.urls import path
from . import views

urlpatterns = [
    path("", views.fatura_listesi, name="fatura_listesi"),
    path("ekle/", views.fatura_ekle, name="fatura_ekle"),
    path("<int:pk>/", views.fatura_detay, name="fatura_detay"),
    path("<int:pk>/duzenle/", views.fatura_duzenle, name="fatura_duzenle"),
    path("<int:pk>/durum/", views.fatura_durum_degistir, name="fatura_durum"),
    path("<int:pk>/pdf/", views.fatura_pdf, name="fatura_pdf"),
    path("<int:pk>/yazdir/", views.fatura_yazdir, name="fatura_yazdir"),
    path("<int:pk>/xml/", views.fatura_xml_indir, name="fatura_xml"),
    path("kdv-ozet/", views.kdv_ozet, name="kdv_ozet"),
]
