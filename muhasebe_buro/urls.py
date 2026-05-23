from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from . import api_views

urlpatterns = [
    path("admin/", admin.site.urls),
    # Kimlik doğrulama
    path("hesap/giris/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("hesap/cikis/", auth_views.LogoutView.as_view(), name="logout"),
    # Mikro Sync REST API
    path("api/v1/ping/", api_views.ping, name="api_ping"),
    path("api/v1/cari/", api_views.cari_listesi, name="api_cari_listesi"),
    path("api/v1/fatura/aktar/", api_views.fatura_aktar, name="api_fatura_aktar"),
    # Uygulamalar
    path("", include("dashboard.urls")),
    path("cari/", include("cari.urls")),
    path("banka/", include("banka.urls")),
    path("sozlesme/", include("sozlesme.urls")),
    path("tahsilat/", include("tahsilat.urls")),
    path("fatura/", include("fatura.urls")),
    path("ceksenet/", include("ceksenet.urls")),
    path("gider/", include("gider.urls")),
    path("stok/", include("stok.urls")),
    path("kasa/", include("kasa.urls")),
    path("rapor/", include("rapor.urls")),
    path("takvim/", include("takvim.urls")),
    path("kullanicilar/", include("kullanici.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
