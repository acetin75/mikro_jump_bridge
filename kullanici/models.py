from django.contrib.auth.models import User
from django.db import models


class AktiviteLogu(models.Model):
    kullanici = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="aktiviteler",
        verbose_name="Kullanıcı",
    )
    tarih = models.DateTimeField("Tarih", auto_now_add=True)
    yol = models.CharField("URL Yolu", max_length=200)
    ip = models.GenericIPAddressField("IP Adresi", null=True, blank=True)

    class Meta:
        ordering = ["-tarih"]
        verbose_name = "Aktivite"
        verbose_name_plural = "Aktivite Logu"

    def __str__(self):
        return f"{self.kullanici} — {self.yol} — {self.tarih:%d.%m.%Y %H:%M}"
