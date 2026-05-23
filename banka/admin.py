from django.contrib import admin
from .models import BankaHesabi, BankaEkstre, BankaHareketi


@admin.register(BankaHesabi)
class BankaHesabiAdmin(admin.ModelAdmin):
    list_display = ["ad", "banka_adi", "hesap_no", "para_birimi", "aktif"]
    list_filter = ["banka_adi", "aktif"]


class BankaHareketiInline(admin.TabularInline):
    model = BankaHareketi
    extra = 0
    fields = ["islem_tarihi", "aciklama", "tutar", "tip", "eslesti", "cari"]


@admin.register(BankaEkstre)
class BankaEkstreAdmin(admin.ModelAdmin):
    list_display = ["banka_hesabi", "yukleme_tarihi", "donem_baslangic", "donem_bitis", "islendi"]
    list_filter = ["banka_hesabi", "islendi"]
    inlines = [BankaHareketiInline]


@admin.register(BankaHareketi)
class BankaHareketiAdmin(admin.ModelAdmin):
    list_display = ["islem_tarihi", "banka_hesabi", "aciklama", "tutar", "tip", "eslesti", "cari"]
    list_filter = ["tip", "eslesti", "banka_hesabi"]
    search_fields = ["aciklama", "referans_no", "cari__ad"]
    date_hierarchy = "islem_tarihi"
