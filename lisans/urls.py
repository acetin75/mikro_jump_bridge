from django.urls import path

from . import views

urlpatterns = [
    path("", views.lisans_durum, name="lisans_durum"),
    path("bitti/", views.lisans_suresi_doldu, name="lisans_suresi_doldu"),
]
