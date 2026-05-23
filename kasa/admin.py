from django.contrib import admin
from .models import KasaHesabi, KasaHareketi


@admin.register(KasaHesabi)
class KasaHesabiAdmin(admin.ModelAdmin):
    list_display = ["ad", "para_birimi", "acilis_bakiyesi", "aktif", "olusturuldu"]
    list_filter = ["aktif", "para_birimi"]
    search_fields = ["ad"]


@admin.register(KasaHareketi)
class KasaHareketiAdmin(admin.ModelAdmin):
    list_display = ["kasa", "tarih", "tip", "tutar", "aciklama", "belge_no", "olusturuldu"]
    list_filter = ["kasa", "tip", "tarih"]
    search_fields = ["aciklama", "belge_no"]
    raw_id_fields = ["tahsilat", "gider", "fatura"]
