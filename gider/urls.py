from django.urls import path
from . import views

app_name = "gider"

urlpatterns = [
    path("", views.gider_listesi, name="list"),
    path("ekle/", views.gider_ekle, name="ekle"),
    path("<int:pk>/duzenle/", views.gider_duzenle, name="duzenle"),
    path("<int:pk>/sil/", views.gider_sil, name="sil"),
    path("kategoriler/", views.kategori_listesi, name="kategoriler"),
]
