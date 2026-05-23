from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="dashboard"),
    path("yedek/indir/", views.yedek_indir, name="yedek_indir"),
    path("yedek/yukle/", views.yedek_yukle, name="yedek_yukle"),
]
