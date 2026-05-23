from django.contrib import admin
from .models import Tahsilat


@admin.register(Tahsilat)
class TahsilatAdmin(admin.ModelAdmin):
    list_display = ["tarih", "cari", "tip", "tutar", "para_birimi", "odeme_yontemi", "belge_no"]
    list_filter = ["tip", "odeme_yontemi", "para_birimi"]
    search_fields = ["cari__ad", "aciklama", "belge_no"]
    date_hierarchy = "tarih"
