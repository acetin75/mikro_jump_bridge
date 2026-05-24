from django.contrib import admin

from .models import MikroCariHesap, MikroFatura, MikroStokKarti


@admin.register(MikroFatura)
class MikroFaturaAdmin(admin.ModelAdmin):
    list_display = ["fat_evrak_seri", "fat_evrak_sira", "fat_tarih", "fat_cari_unvan", "fat_toplam", "tip", "durum"]
    list_filter = ["durum", "tip", "firma_ayar"]
    search_fields = ["fat_guid", "fat_cari_unvan", "fat_evrak_seri"]
    readonly_fields = ["fat_guid", "ham_json", "olusturuldu", "guncellendi"]


@admin.register(MikroCariHesap)
class MikroCariHesapAdmin(admin.ModelAdmin):
    list_display = ["cari_kod", "cari_unvan", "cari_vkn", "guncel_bakiye", "son_guncelleme"]
    search_fields = ["cari_kod", "cari_unvan", "cari_vkn"]


@admin.register(MikroStokKarti)
class MikroStokKartiAdmin(admin.ModelAdmin):
    list_display = ["stok_kod", "stok_isim", "stok_birimi", "satis_fiyati"]
    search_fields = ["stok_kod", "stok_isim"]
