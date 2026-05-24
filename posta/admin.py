from django.contrib import admin

from .models import EkstreGonderimLog, MailAyar


@admin.register(MailAyar)
class MailAyarAdmin(admin.ModelAdmin):
    list_display = ["kullanici", "smtp_sunucu", "smtp_port", "tls_kullan", "aktif", "guncellendi"]
    list_filter = ["aktif", "tls_kullan"]
    search_fields = ["kullanici", "smtp_sunucu", "gonderen_email"]
    readonly_fields = ["guncellendi"]
    exclude = ["_sifre_sifreli"]


@admin.register(EkstreGonderimLog)
class EkstreGonderimLogAdmin(admin.ModelAdmin):
    list_display = [
        "cari_kod", "cari_unvan", "alici_email",
        "firma_ayar", "donem_baslangic", "donem_bitis", "durum", "olusturuldu",
    ]
    list_filter = ["durum", "firma_ayar"]
    search_fields = ["cari_kod", "cari_unvan", "alici_email"]
    readonly_fields = [
        "firma_ayar", "cari_kod", "cari_unvan", "alici_email",
        "donem_baslangic", "donem_bitis", "konu", "durum", "hata_mesaji", "olusturuldu",
    ]
