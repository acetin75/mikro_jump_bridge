from django.urls import path

from . import views

app_name = "kullanici"

urlpatterns = [
    path("", views.kullanici_listesi, name="liste"),
    path("ekle/", views.kullanici_ekle, name="ekle"),
    path("<int:pk>/duzenle/", views.kullanici_duzenle, name="duzenle"),
    path("aktivite/", views.aktivite_logu, name="aktivite"),
]
