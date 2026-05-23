from django.contrib import admin
from .models import Sozlesme


@admin.register(Sozlesme)
class SozlesmeAdmin(admin.ModelAdmin):
    list_display = ["sozlesme_no", "baslik", "cari", "durum", "baslangic_tarihi", "bitis_tarihi", "tutar"]
    list_filter = ["durum", "para_birimi"]
    search_fields = ["baslik", "sozlesme_no", "cari__ad"]
