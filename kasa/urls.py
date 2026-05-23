from django.urls import path
from . import views

app_name = "kasa"

urlpatterns = [
    path("",                          views.kasa_listesi,  name="list"),
    path("ekle/",                     views.kasa_ekle,     name="ekle"),
    path("<int:pk>/",                 views.kasa_detay,    name="detay"),
    path("<int:pk>/duzenle/",         views.kasa_duzenle,  name="duzenle"),
    path("<int:pk>/sil/",             views.kasa_sil,      name="sil"),
    path("<int:pk>/hareket/ekle/",    views.hareket_ekle,  name="hareket_ekle"),
    path("hareket/<int:pk>/sil/",     views.hareket_sil,   name="hareket_sil"),
]
