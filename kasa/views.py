import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from .models import KasaHesabi, KasaHareketi
from .forms import KasaHesabiForm, KasaHareketiForm

logger = logging.getLogger("muhasebe")


# ── Kasa Listesi ─────────────────────────────────────────────────────────────

def kasa_listesi(request):
    kasalar = KasaHesabi.objects.all()
    return render(request, "kasa/list.html", {"kasalar": kasalar})


# ── Kasa Hesabı CRUD ─────────────────────────────────────────────────────────

def kasa_ekle(request):
    form = KasaHesabiForm(request.POST or None)
    if form.is_valid():
        kasa = form.save()
        logger.info("Kasa hesabı oluşturuldu: %s", kasa.ad)
        messages.success(request, f"'{kasa.ad}' kasa hesabı oluşturuldu.")
        return redirect("kasa:detay", pk=kasa.pk)
    return render(request, "kasa/hesap_form.html", {"form": form, "baslik": "Yeni Kasa Hesabı"})


def kasa_detay(request, pk):
    kasa = get_object_or_404(KasaHesabi, pk=pk)
    hareketler = kasa.hareketler.select_related("tahsilat__cari", "gider", "fatura").all()

    # Tarih filtresi
    ay = request.GET.get("ay", "")
    if ay:
        try:
            yil, mon = ay.split("-")
            hareketler = hareketler.filter(tarih__year=yil, tarih__month=mon)
        except ValueError:
            pass

    return render(request, "kasa/detay.html", {
        "kasa": kasa,
        "hareketler": hareketler,
        "ay": ay,
    })


def kasa_duzenle(request, pk):
    kasa = get_object_or_404(KasaHesabi, pk=pk)
    form = KasaHesabiForm(request.POST or None, instance=kasa)
    if form.is_valid():
        form.save()
        messages.success(request, "Kasa hesabı güncellendi.")
        return redirect("kasa:detay", pk=pk)
    return render(request, "kasa/hesap_form.html", {
        "form": form, "baslik": "Kasa Düzenle", "kasa": kasa
    })


def kasa_sil(request, pk):
    kasa = get_object_or_404(KasaHesabi, pk=pk)
    if request.method == "POST":
        ad = kasa.ad
        kasa.delete()
        logger.info("Kasa hesabı silindi: %s", ad)
        messages.success(request, f"'{ad}' kasa hesabı silindi.")
        return redirect("kasa:list")
    return render(request, "confirm_delete.html", {
        "nesne": kasa,
        "mesaj": f"'{kasa.ad}' kasa hesabını ve tüm hareketlerini silmek istiyor musunuz?",
        "geri_url": "kasa:detay",
        "geri_pk": kasa.pk,
    })


# ── Kasa Hareketi ────────────────────────────────────────────────────────────

def hareket_ekle(request, pk):
    """Manuel kasa hareketi ekle."""
    kasa = get_object_or_404(KasaHesabi, pk=pk)
    initial = {
        "kasa": kasa,
        "tarih": timezone.now().date(),
    }
    form = KasaHareketiForm(request.POST or None, initial=initial)
    if form.is_valid():
        hareket = form.save()
        logger.info("Kasa hareketi eklendi: %s — %s ₺", kasa.ad, hareket.tutar)
        messages.success(request, "Kasa hareketi kaydedildi.")
        return redirect("kasa:detay", pk=pk)
    return render(request, "kasa/hareket_form.html", {
        "form": form,
        "kasa": kasa,
        "baslik": "Manuel Kasa Hareketi",
    })


def hareket_sil(request, pk):
    hareket = get_object_or_404(KasaHareketi, pk=pk)
    kasa_pk = hareket.kasa_id
    if hareket.otomatik_mi:
        messages.error(request, "Otomatik oluşturulan hareketler silinemez. Kaynak kaydı silin.")
        return redirect("kasa:detay", pk=kasa_pk)
    if request.method == "POST":
        hareket.delete()
        messages.success(request, "Kasa hareketi silindi.")
        return redirect("kasa:detay", pk=kasa_pk)
    return render(request, "confirm_delete.html", {
        "nesne": hareket,
        "mesaj": f"{hareket.tutar} ₺ tutarındaki hareketi silmek istiyor musunuz?",
        "geri_url": "kasa:detay",
        "geri_pk": kasa_pk,
    })
