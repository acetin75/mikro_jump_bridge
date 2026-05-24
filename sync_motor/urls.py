from django.urls import path

from . import views

urlpatterns = [
    path("", views.anasayfa, name="anasayfa"),
    path("firmalar/", views.firma_liste, name="firma_liste"),
    path("firmalar/ekle/", views.firma_ekle, name="firma_ekle"),
    path("firmalar/<int:pk>/duzenle/", views.firma_duzenle, name="firma_duzenle"),
    path("firmalar/<int:pk>/test/", views.firma_test, name="firma_test"),
    path("importlar/", views.import_liste, name="import_liste"),
    path("import/<int:firma_pk>/baslat/", views.import_baslat, name="import_baslat"),
]
