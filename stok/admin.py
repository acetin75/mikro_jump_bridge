from django.contrib import admin
from .models import Urun, StokHareketi


@admin.register(Urun)
class UrunAdmin(admin.ModelAdmin):
    list_display = ["kod", "ad", "birim", "kdv_orani", "satis_fiyati", "min_stok", "aktif"]
    list_filter = ["aktif", "kdv_orani", "birim"]
    search_fields = ["kod", "ad"]
    list_editable = ["aktif"]


@admin.register(StokHareketi)
class StokHareketiAdmin(admin.ModelAdmin):
    list_display = ["tarih", "urun", "tip", "miktar", "belge_no", "aciklama"]
    list_filter = ["tip", "tarih"]
    search_fields = ["urun__ad", "urun__kod", "belge_no"]
    date_hierarchy = "tarih"
