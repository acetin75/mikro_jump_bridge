from django.urls import path
from . import views

app_name = "stok"

urlpatterns = [
    path("", views.urun_listesi, name="list"),
    path("ekle/", views.urun_ekle, name="urun_ekle"),
    path("<int:pk>/", views.urun_detay, name="urun_detay"),
    path("<int:pk>/duzenle/", views.urun_duzenle, name="urun_duzenle"),
    path("<int:pk>/sil/", views.urun_sil, name="urun_sil"),
    path("hareket/ekle/", views.stok_hareketi_ekle, name="hareket_ekle"),
    path("hareket/<int:urun_pk>/ekle/", views.stok_hareketi_ekle, name="hareket_ekle_urun"),
    path("hareket/<int:pk>/sil/", views.stok_hareketi_sil, name="hareket_sil"),
    path("degerleme/", views.stok_degerleme_raporu, name="degerleme"),
    path("degerleme/excel/", views.stok_degerleme_excel, name="degerleme_excel"),
]
