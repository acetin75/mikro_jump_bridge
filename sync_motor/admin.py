from django.contrib import admin
from .models import FirmaAyar, ImportLog


@admin.register(FirmaAyar)
class FirmaAyarAdmin(admin.ModelAdmin):
    list_display = ["ad", "baglanti_tipi", "mikro_sunucu", "aktif", "guncellendi"]
    list_filter = ["baglanti_tipi", "aktif"]
    search_fields = ["ad", "mikro_sunucu"]


@admin.register(ImportLog)
class ImportLogAdmin(admin.ModelAdmin):
    list_display = ["pk", "firma_ayar", "durum", "cekilen_adet", "aktarilan_adet", "olusturuldu"]
    list_filter = ["durum", "firma_ayar"]
    readonly_fields = ["olusturuldu", "guncellendi"]
