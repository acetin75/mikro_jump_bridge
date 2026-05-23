import logging

from django.contrib import messages
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render

from muhasebe_buro.permissions import yonetici_gerekli

from .forms import KullaniciForm
from .models import AktiviteLogu

logger = logging.getLogger("muhasebe")


@yonetici_gerekli
def kullanici_listesi(request):
    kullanicilar = User.objects.prefetch_related("groups").order_by("username")
    return render(request, "kullanici/liste.html", {"kullanicilar": kullanicilar})


@yonetici_gerekli
def kullanici_ekle(request):
    if request.method == "POST":
        form = KullaniciForm(request.POST)
        if form.is_valid():
            try:
                kullanici = form.save()
                messages.success(request, f"'{kullanici.username}' kullanıcısı oluşturuldu.")
                logger.info("Kullanıcı oluşturuldu: %s", kullanici.username)
                return redirect("kullanici:liste")
            except Exception as e:
                logger.error("Kullanıcı oluşturma hatası: %s", e, exc_info=True)
                messages.error(request, "Kullanıcı oluşturulurken hata oluştu.")
    else:
        form = KullaniciForm()
    return render(request, "kullanici/form.html", {"form": form, "baslik": "Yeni Kullanıcı"})


@yonetici_gerekli
def kullanici_duzenle(request, pk):
    kullanici = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        form = KullaniciForm(request.POST, instance=kullanici)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, f"'{kullanici.username}' güncellendi.")
                logger.info("Kullanıcı güncellendi: %s", kullanici.username)
                return redirect("kullanici:liste")
            except Exception as e:
                logger.error("Kullanıcı güncelleme hatası: %s", e, exc_info=True)
                messages.error(request, "Güncelleme sırasında hata oluştu.")
    else:
        form = KullaniciForm(instance=kullanici)
    return render(request, "kullanici/form.html", {
        "form": form,
        "baslik": f"{kullanici.username} — Düzenle",
        "kullanici": kullanici,
    })


@yonetici_gerekli
def aktivite_logu(request):
    loglar = AktiviteLogu.objects.select_related("kullanici").all()[:500]
    return render(request, "kullanici/aktivite.html", {"loglar": loglar})
