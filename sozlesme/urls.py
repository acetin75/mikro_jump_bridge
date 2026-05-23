from django.urls import path
from . import views

urlpatterns = [
    path("", views.sozlesme_listesi, name="sozlesme_listesi"),
    path("ekle/", views.sozlesme_ekle, name="sozlesme_ekle"),
    path("<int:pk>/", views.sozlesme_detay, name="sozlesme_detay"),
    path("<int:pk>/duzenle/", views.sozlesme_duzenle, name="sozlesme_duzenle"),
]
