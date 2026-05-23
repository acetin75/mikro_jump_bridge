from django.contrib import admin
from .models import Gider, GiderKategori


@admin.register(GiderKategori)
class GiderKategoriAdmin(admin.ModelAdmin):
    list_display = ("ad",)


@admin.register(Gider)
class GiderAdmin(admin.ModelAdmin):
    list_display = ("tarih", "aciklama", "kategori", "kdv_haric_tutar", "kdv_orani", "odeme_yontemi")
    list_filter = ("kategori", "odeme_yontemi")
