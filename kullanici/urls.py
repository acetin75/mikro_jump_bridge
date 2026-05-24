from django.urls import path

from . import views

urlpatterns = [
    path("", views.kullanici_liste, name="kullanici_liste"),
    path("ekle/", views.kullanici_ekle, name="kullanici_ekle"),
    path("<int:pk>/sil/", views.kullanici_sil, name="kullanici_sil"),
    path("<int:pk>/yetki/", views.kullanici_yetki, name="kullanici_yetki"),
    path("<int:pk>/sifre/", views.kullanici_sifre_degistir, name="kullanici_sifre"),
]
