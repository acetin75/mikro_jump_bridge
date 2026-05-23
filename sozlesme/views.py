from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q
from .models import Sozlesme
from .forms import SozlesmeForm


def sozlesme_listesi(request):
    q = request.GET.get("q", "")
    durum = request.GET.get("durum", "")
    sozlesmeler = Sozlesme.objects.select_related("cari").all()
    if q:
        sozlesmeler = sozlesmeler.filter(
            Q(baslik__icontains=q) | Q(sozlesme_no__icontains=q) | Q(cari__ad__icontains=q)
        )
    if durum:
        sozlesmeler = sozlesmeler.filter(durum=durum)
    return render(request, "sozlesme/list.html", {
        "sozlesmeler": sozlesmeler, "q": q, "durum": durum
    })


def sozlesme_detay(request, pk):
    sozlesme = get_object_or_404(Sozlesme.objects.select_related("cari"), pk=pk)
    return render(request, "sozlesme/detail.html", {"sozlesme": sozlesme})


def sozlesme_ekle(request):
    form = SozlesmeForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        s = form.save()
        messages.success(request, f"Sözleşme '{s}' oluşturuldu.")
        return redirect("sozlesme_detay", pk=s.pk)
    return render(request, "sozlesme/form.html", {"form": form, "baslik": "Yeni Sözleşme"})


def sozlesme_duzenle(request, pk):
    sozlesme = get_object_or_404(Sozlesme, pk=pk)
    form = SozlesmeForm(request.POST or None, request.FILES or None, instance=sozlesme)
    if form.is_valid():
        form.save()
        messages.success(request, "Sözleşme güncellendi.")
        return redirect("sozlesme_detay", pk=pk)
    return render(request, "sozlesme/form.html", {"form": form, "baslik": "Sözleşme Düzenle"})
