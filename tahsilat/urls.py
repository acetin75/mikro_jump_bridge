from django.urls import path
from . import views

urlpatterns = [
    path("", views.tahsilat_listesi, name="tahsilat_listesi"),
    path("ekle/", views.tahsilat_ekle, name="tahsilat_ekle"),
    path("<int:pk>/sil/", views.tahsilat_sil, name="tahsilat_sil"),
]
