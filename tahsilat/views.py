from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db import transaction
from django.db.models import Q, Sum
from .models import Tahsilat
from .forms import TahsilatForm
from cari.models import HesapHareketi
from kasa.utils import tahsilat_kasa_hareketi_olustur


def tahsilat_listesi(request):
    q = request.GET.get("q", "")
    tip = request.GET.get("tip", "")
    kayitlar = Tahsilat.objects.select_related("cari").all()
    if q:
        kayitlar = kayitlar.filter(Q(cari__ad__icontains=q) | Q(aciklama__icontains=q))
    if tip:
        kayitlar = kayitlar.filter(tip=tip)
    toplam = kayitlar.aggregate(Sum("tutar"))["tutar__sum"] or 0
    return render(request, "tahsilat/list.html", {
        "kayitlar": kayitlar, "q": q, "tip": tip, "toplam": toplam
    })


def tahsilat_ekle(request):
    form = TahsilatForm(request.POST or None)
    if form.is_valid():
        with transaction.atomic():
            t = form.save()
            # Cari hesap hareketine de otomatik yaz
            HesapHareketi.objects.create(
                cari=t.cari,
                tarih=t.tarih,
                aciklama=t.aciklama or t.get_tip_display(),
                belge_no=t.belge_no,
                hareket_tipi="tahsilat" if t.tip == "tahsilat" else "odeme",
                alacak=t.tutar if t.tip == "tahsilat" else 0,
                borc=t.tutar if t.tip == "odeme" else 0,
                para_birimi=t.para_birimi,
            )
            # Nakit ise kasa hareketi oluştur
            tahsilat_kasa_hareketi_olustur(t)
        messages.success(request, "Kayıt oluşturuldu ve cari hesaba işlendi.")
        return redirect("tahsilat_listesi")
    return render(request, "tahsilat/form.html", {"form": form, "baslik": "Yeni Tahsilat / Ödeme"})


def tahsilat_sil(request, pk):
    kayit = get_object_or_404(Tahsilat, pk=pk)
    if request.method == "POST":
        kayit.delete()
        messages.success(request, "Kayıt silindi.")
        return redirect("tahsilat_listesi")
    return render(request, "confirm_delete.html", {"nesne": kayit, "geri_url": "tahsilat_listesi"})
