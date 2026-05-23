from django.contrib import admin
from .models import Fatura, FaturaKalemi


class FaturaKalemiInline(admin.TabularInline):
    model = FaturaKalemi
    extra = 1
    fields = ["sira", "aciklama", "miktar", "birim", "birim_fiyat", "kdv_orani", "iskonto_oran"]


@admin.register(Fatura)
class FaturaAdmin(admin.ModelAdmin):
    list_display = ["fatura_no", "cari", "tip", "tarih", "vade_tarihi", "durum", "para_birimi"]
    list_filter = ["tip", "durum", "para_birimi"]
    search_fields = ["fatura_no", "cari__ad", "aciklama"]
    date_hierarchy = "tarih"
    inlines = [FaturaKalemiInline]
