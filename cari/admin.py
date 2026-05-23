from django.contrib import admin
from .models import Cari, HesapHareketi


class HesapHareketiInline(admin.TabularInline):
    model = HesapHareketi
    extra = 0
    fields = ["tarih", "belge_no", "aciklama", "hareket_tipi", "borc", "alacak"]


@admin.register(Cari)
class CariAdmin(admin.ModelAdmin):
    list_display = ["ad", "tip", "vergi_no", "telefon", "aktif"]
    list_filter = ["tip", "aktif"]
    search_fields = ["ad", "vergi_no"]
    inlines = [HesapHareketiInline]


@admin.register(HesapHareketi)
class HesapHareketiAdmin(admin.ModelAdmin):
    list_display = ["tarih", "cari", "belge_no", "aciklama", "borc", "alacak"]
    list_filter = ["hareket_tipi", "para_birimi"]
    search_fields = ["cari__ad", "aciklama", "belge_no"]
    date_hierarchy = "tarih"
