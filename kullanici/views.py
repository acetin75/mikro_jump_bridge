import logging
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render

from .forms import KullaniciEkleForm, SifreDegistirForm

logger = logging.getLogger("mikro_sync")


def yonetici_gerekli(view_func):
    """Sadece superuser erişebilir; aksi hâlde ana sayfaya yönlendir."""

    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_superuser:
            messages.error(request, "Bu sayfaya erişim yetkiniz yok.")
            return redirect("anasayfa")
        return view_func(request, *args, **kwargs)

    return _wrapped


@yonetici_gerekli
def kullanici_liste(request):
    kullanicilar = User.objects.all().order_by("username")
    return render(request, "kullanici/liste.html", {"kullanicilar": kullanicilar})


@yonetici_gerekli
def kullanici_ekle(request):
    if request.method == "POST":
        form = KullaniciEkleForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            ad_bolundu = cd["ad_soyad"].split(" ", 1) if cd["ad_soyad"] else ["", ""]
            first_name = ad_bolundu[0]
            last_name = ad_bolundu[1] if len(ad_bolundu) > 1 else ""

            kullanici = User.objects.create_user(
                username=cd["kullanici_adi"],
                email=cd.get("email", ""),
                password=cd["sifre"],
                first_name=first_name,
                last_name=last_name,
            )
            if cd["yonetici"]:
                kullanici.is_superuser = True
                kullanici.is_staff = True
                kullanici.save()

            logger.info("Yeni kullanıcı oluşturuldu: %s (yönetici=%s)", kullanici.username, cd["yonetici"])
            messages.success(request, f"'{kullanici.username}' kullanıcısı oluşturuldu.")
            return redirect("kullanici_liste")
    else:
        form = KullaniciEkleForm()

    return render(request, "kullanici/ekle.html", {"form": form})


@yonetici_gerekli
def kullanici_sil(request, pk):
    kullanici = get_object_or_404(User, pk=pk)

    if kullanici == request.user:
        messages.error(request, "Kendi hesabınızı silemezsiniz.")
        return redirect("kullanici_liste")

    if request.method == "POST":
        ad = kullanici.username
        kullanici.delete()
        logger.info("Kullanıcı silindi: %s", ad)
        messages.success(request, f"'{ad}' kullanıcısı silindi.")
        return redirect("kullanici_liste")

    return render(request, "kullanici/sil_onayla.html", {"kullanici": kullanici})


@yonetici_gerekli
def kullanici_yetki(request, pk):
    """Yönetici yetkisini açar / kapar (POST)."""
    kullanici = get_object_or_404(User, pk=pk)

    if kullanici == request.user:
        messages.error(request, "Kendi yetkinizi değiştiremezsiniz.")
        return redirect("kullanici_liste")

    if request.method == "POST":
        kullanici.is_superuser = not kullanici.is_superuser
        kullanici.is_staff = kullanici.is_superuser
        kullanici.save()
        durum = "Yönetici" if kullanici.is_superuser else "Standart Kullanıcı"
        logger.info("Kullanıcı yetkisi değiştirildi: %s → %s", kullanici.username, durum)
        messages.success(request, f"'{kullanici.username}' artık {durum}.")
        return redirect("kullanici_liste")

    return redirect("kullanici_liste")


@yonetici_gerekli
def kullanici_sifre_degistir(request, pk):
    kullanici = get_object_or_404(User, pk=pk)

    if request.method == "POST":
        form = SifreDegistirForm(request.POST)
        if form.is_valid():
            kullanici.set_password(form.cleaned_data["yeni_sifre"])
            kullanici.save()
            logger.info("Kullanıcı şifresi değiştirildi: %s", kullanici.username)
            messages.success(request, f"'{kullanici.username}' şifresi güncellendi.")
            return redirect("kullanici_liste")
    else:
        form = SifreDegistirForm()

    return render(request, "kullanici/sifre_degistir.html", {"form": form, "kullanici": kullanici})
