from django.urls import path

from . import views

urlpatterns = [
    path("", views.posta_ayarlar, name="posta_ayarlar"),
    path("test/", views.posta_test, name="posta_test"),
    path("gecmis/", views.posta_gecmis, name="posta_gecmis"),
    path("ekstre-gonder/", views.cari_ekstre_gonder, name="posta_ekstre_gonder"),
]
