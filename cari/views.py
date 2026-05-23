from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q, Sum
from django.utils import timezone
from django.conf import settings
from decimal import Decimal
from .models import Cari, HesapHareketi
from .forms import CariForm, HesapHareketiCariForm, HesapHareketiForm


def cari_listesi(request):
    q = request.GET.get("q", "")
    tip = request.GET.get("tip", "")
    cariler = Cari.objects.all()
    if q:
        cariler = cariler.filter(Q(ad__icontains=q) | Q(vergi_no__icontains=q))
    if tip:
        cariler = cariler.filter(tip=tip)
    return render(request, "cari/list.html", {"cariler": cariler, "q": q, "tip": tip})


def cari_detay(request, pk):
    cari = get_object_or_404(Cari, pk=pk)
    hareketler = cari.hareketler.all()
    form = HesapHareketiCariForm()
    if request.method == "POST":
        form = HesapHareketiCariForm(request.POST)
        if form.is_valid():
            hareket = form.save(commit=False)
            hareket.cari = cari
            hareket.save()
            messages.success(request, "Hareket kaydedildi.")
            return redirect("cari_detay", pk=pk)
    return render(request, "cari/detail.html", {
        "cari": cari,
        "hareketler": hareketler,
        "form": form,
    })


def cari_ekle(request):
    form = CariForm(request.POST or None)
    if form.is_valid():
        cari = form.save()
        messages.success(request, f"'{cari.ad}' oluşturuldu.")
        return redirect("cari_detay", pk=cari.pk)
    return render(request, "cari/form.html", {"form": form, "baslik": "Yeni Cari"})


def cari_duzenle(request, pk):
    cari = get_object_or_404(Cari, pk=pk)
    form = CariForm(request.POST or None, instance=cari)
    if form.is_valid():
        form.save()
        messages.success(request, "Cari güncellendi.")
        return redirect("cari_detay", pk=pk)
    return render(request, "cari/form.html", {"form": form, "baslik": "Cari Düzenle", "cari": cari})


def hareket_listesi(request):
    q = request.GET.get("q", "")
    hareketler = HesapHareketi.objects.select_related("cari").all()
    if q:
        hareketler = hareketler.filter(
            Q(cari__ad__icontains=q) | Q(aciklama__icontains=q) | Q(belge_no__icontains=q)
        )
    return render(request, "cari/hareket_list.html", {"hareketler": hareketler, "q": q})


def hareket_ekle(request):
    form = HesapHareketiForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Hareket kaydedildi.")
        return redirect("hareket_listesi")
    return render(request, "cari/hareket_form.html", {"form": form, "baslik": "Yeni Hareket"})


def hareket_sil(request, pk):
    hareket = get_object_or_404(HesapHareketi, pk=pk)
    if request.method == "POST":
        cari_pk = hareket.cari_id
        hareket.delete()
        messages.success(request, "Hareket silindi.")
        return redirect("cari_detay", pk=cari_pk)
    return render(request, "confirm_delete.html", {"nesne": hareket, "geri_url": "cari_listesi"})


def cari_mutabakat(request, pk):
    """Cari mutabakat mektubu — yazdirma/PDF sayfasi."""
    cari = get_object_or_404(Cari, pk=pk)
    baslangic_str = request.GET.get("baslangic", "")
    bitis_str = request.GET.get("bitis", "")

    bugun = timezone.now().date()
    # Varsayılan: bu yılın başından bugüne
    try:
        from datetime import date
        baslangic = date.fromisoformat(baslangic_str) if baslangic_str else date(bugun.year, 1, 1)
        bitis = date.fromisoformat(bitis_str) if bitis_str else bugun
    except ValueError:
        from datetime import date
        baslangic = date(bugun.year, 1, 1)
        bitis = bugun

    hareketler = cari.hareketler.filter(tarih__gte=baslangic, tarih__lte=bitis).order_by("tarih")
    toplam_borc = hareketler.aggregate(t=Sum("borc"))["t"] or Decimal("0")
    toplam_alacak = hareketler.aggregate(t=Sum("alacak"))["t"] or Decimal("0")
    bakiye = toplam_borc - toplam_alacak

    ctx = {
        "cari": cari,
        "hareketler": hareketler,
        "baslangic": baslangic,
        "bitis": bitis,
        "bugun": bugun,
        "toplam_borc": toplam_borc,
        "toplam_alacak": toplam_alacak,
        "bakiye": bakiye,
        "firma_adi": getattr(settings, "FIRMA_ADI", "Firma Adı"),
        "firma_vkn": getattr(settings, "FIRMA_VKN", ""),
        "firma_vergi_dairesi": getattr(settings, "FIRMA_VERGI_DAIRESI", ""),
        "firma_adres": getattr(settings, "FIRMA_ADRES", ""),
    }
    return render(request, "cari/mutabakat_print.html", ctx)
