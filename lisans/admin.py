from django.contrib import admin
from .models import LisansBilgisi


@admin.register(LisansBilgisi)
class LisansBilgisiAdmin(admin.ModelAdmin):
    list_display  = ["lisans_tipi", "musteri_kodu", "install_tarihi", "lisans_bitis", "gecerlilik_durumu"]
    readonly_fields = ["install_tarihi", "guncellendi", "gecerlilik_durumu", "kalan_gun"]
