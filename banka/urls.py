from django.urls import path
from . import views

urlpatterns = [
    path("hesaplar/", views.hesap_listesi, name="banka_hesap_listesi"),
    path("hesaplar/ekle/", views.hesap_ekle, name="banka_hesap_ekle"),
    path("hesaplar/<int:pk>/duzenle/", views.hesap_duzenle, name="banka_hesap_duzenle"),
    path("ekstreler/", views.ekstre_listesi, name="banka_ekstre_listesi"),
    path("ekstreler/yukle/", views.ekstre_yukle, name="banka_ekstre_yukle"),
    path("ekstreler/<int:pk>/", views.ekstre_detay, name="banka_ekstre_detay"),
    path("hareketler/", views.hareket_listesi, name="banka_hareket_listesi"),
    path("hareketler/ekle/", views.hareket_ekle, name="banka_hareket_ekle"),
    path("hareketler/<int:pk>/eslestir/", views.hareket_eslestir, name="banka_hareket_eslestir"),
]
