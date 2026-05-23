from django.contrib import admin

from .models import AktiviteLogu


@admin.register(AktiviteLogu)
class AktiviteLoguAdmin(admin.ModelAdmin):
    list_display = ["tarih", "kullanici", "yol", "ip"]
    list_filter = ["kullanici"]
    search_fields = ["kullanici__username", "yol"]
    readonly_fields = ["tarih", "kullanici", "yol", "ip"]
