from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db import transaction
from .models import Gider, GiderKategori
from .forms import GiderForm, GiderKategoriForm
from kasa.utils import gider_kasa_hareketi_olustur


def gider_listesi(request):
    qs = Gider.objects.select_related("kategori").all()

    ay = request.GET.get("ay", "")
    kategori_id = request.GET.get("kategori", "")

    if ay:
        yil, mon = ay.split("-")
        qs = qs.filter(tarih__year=yil, tarih__month=mon)
    if kategori_id:
        qs = qs.filter(kategori_id=kategori_id)

    from decimal import Decimal
    toplam_kdv_haric = sum(g.kdv_haric_tutar for g in qs) or Decimal("0")
    toplam_kdv = sum(g.kdv_tutari for g in qs) or Decimal("0")
    toplam_kdv_dahil = sum(g.kdv_dahil_tutar for g in qs) or Decimal("0")

    context = {
        "giderler": qs,
        "kategoriler": GiderKategori.objects.all(),
        "ay": ay,
        "kategori_id": kategori_id,
        "toplam_kdv_haric": toplam_kdv_haric,
        "toplam_kdv": toplam_kdv,
        "toplam_kdv_dahil": toplam_kdv_dahil,
    }
    return render(request, "gider/list.html", context)


def gider_ekle(request):
    form = GiderForm(request.POST or None)
    if form.is_valid():
        with transaction.atomic():
            gider = form.save()
            gider_kasa_hareketi_olustur(gider)
        messages.success(request, "Gider kaydedildi.")
        return redirect("gider:list")
    return render(request, "gider/form.html", {"form": form, "baslik": "Yeni Gider"})


def gider_duzenle(request, pk):
    obj = get_object_or_404(Gider, pk=pk)
    form = GiderForm(request.POST or None, instance=obj)
    if form.is_valid():
        form.save()
        messages.success(request, "Gider güncellendi.")
        return redirect("gider:list")
    return render(request, "gider/form.html", {"form": form, "baslik": "Gider Düzenle", "obj": obj})


def gider_sil(request, pk):
    obj = get_object_or_404(Gider, pk=pk)
    if request.method == "POST":
        obj.delete()
        messages.success(request, "Gider silindi.")
        return redirect("gider:list")
    return render(request, "confirm_delete.html", {"obj": obj, "mesaj": f"'{obj.aciklama}' giderini silmek istiyor musunuz?"})


def kategori_listesi(request):
    form = GiderKategoriForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Kategori eklendi.")
        return redirect("gider:kategoriler")
    kategoriler = GiderKategori.objects.all()
    return render(request, "gider/kategoriler.html", {"form": form, "kategoriler": kategoriler})
