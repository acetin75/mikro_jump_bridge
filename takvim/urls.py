from django.urls import path

from . import views

app_name = "takvim"

urlpatterns = [
    path("", views.takvim, name="takvim"),
]
