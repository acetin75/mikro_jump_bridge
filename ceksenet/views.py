from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from .models import CekSenet
from .forms import CekSenetForm


def ceksenet_listesi(request):
    qs = CekSenet.objects.select_related("cari").all()

    tip = request.GET.get("tip", "")
    durum = request.GET.get("durum", "")
    vadeli = request.GET.get("vadeli", "")

    if tip:
        qs = qs.filter(tip=tip)
    if durum:
        qs = qs.filter(durum=durum)
    if vadeli:
        qs = qs.filter(durum="beklemede", vade_tarihi__lt=timezone.now().date())

    today = timezone.now().date()
    context = {
        "ceksenets": qs,
        "today": today,
        "tip_secili": tip,
        "durum_secili": durum,
        "vadeli": vadeli,
    }
    return render(request, "ceksenet/list.html", context)


def ceksenet_ekle(request):
    form = CekSenetForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Çek/Senet kaydedildi.")
        return redirect("ceksenet:list")
    return render(request, "ceksenet/form.html", {"form": form, "baslik": "Yeni Çek/Senet"})


def ceksenet_duzenle(request, pk):
    obj = get_object_or_404(CekSenet, pk=pk)
    form = CekSenetForm(request.POST or None, instance=obj)
    if form.is_valid():
        form.save()
        messages.success(request, "Çek/Senet güncellendi.")
        return redirect("ceksenet:list")
    return render(request, "ceksenet/form.html", {"form": form, "baslik": "Çek/Senet Düzenle", "obj": obj})


def ceksenet_sil(request, pk):
    obj = get_object_or_404(CekSenet, pk=pk)
    if request.method == "POST":
        obj.delete()
        messages.success(request, "Çek/Senet silindi.")
        return redirect("ceksenet:list")
    return render(request, "confirm_delete.html", {"obj": obj, "mesaj": f"'{obj}' kaydını silmek istediğinize emin misiniz?"})


def ceksenet_durum_degistir(request, pk):
    if request.method == "POST":
        obj = get_object_or_404(CekSenet, pk=pk)
        obj.durum = request.POST.get("durum", obj.durum)
        obj.save()
        messages.success(request, "Durum güncellendi.")
    return redirect("ceksenet:list")
