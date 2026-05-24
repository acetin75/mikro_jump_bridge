from django.urls import path

from . import views

urlpatterns = [
    path("faturalar/", views.fatura_liste, name="mikro_fatura_liste"),
    path("faturalar/<int:pk>/", views.fatura_detay, name="mikro_fatura_detay"),
]
