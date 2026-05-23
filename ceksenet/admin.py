from django.contrib import admin
from .models import CekSenet


@admin.register(CekSenet)
class CekSenetAdmin(admin.ModelAdmin):
    list_display = ("belge_no", "cari", "tip", "tutar", "vade_tarihi", "durum")
    list_filter = ("tip", "durum")
    search_fields = ("belge_no", "cari__unvan")
