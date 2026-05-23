from django.urls import path
from . import views

urlpatterns = [
    path("", views.cari_listesi, name="cari_listesi"),
    path("ekle/", views.cari_ekle, name="cari_ekle"),
    path("<int:pk>/", views.cari_detay, name="cari_detay"),
    path("<int:pk>/duzenle/", views.cari_duzenle, name="cari_duzenle"),
    path("<int:pk>/mutabakat/", views.cari_mutabakat, name="cari_mutabakat"),
    path("hareketler/", views.hareket_listesi, name="hareket_listesi"),
    path("hareketler/ekle/", views.hareket_ekle, name="hareket_ekle"),
    path("hareketler/<int:pk>/sil/", views.hareket_sil, name="hareket_sil"),
]
