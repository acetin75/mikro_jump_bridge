from django.urls import path
from . import views

app_name = "ceksenet"

urlpatterns = [
    path("", views.ceksenet_listesi, name="list"),
    path("ekle/", views.ceksenet_ekle, name="ekle"),
    path("<int:pk>/duzenle/", views.ceksenet_duzenle, name="duzenle"),
    path("<int:pk>/sil/", views.ceksenet_sil, name="sil"),
    path("<int:pk>/durum/", views.ceksenet_durum_degistir, name="durum"),
]
