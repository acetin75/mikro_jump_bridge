from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from .models import BankaHesabi, BankaEkstre, BankaHareketi
from .forms import BankaHesabiForm, BankaEkstreYukleForm, BankaHareketiForm, EslestirForm
from .parser import parse_ekstre


# ── Banka Hesapları ─────────────────────────────────────────────────────────

def hesap_listesi(request):
    hesaplar = BankaHesabi.objects.all()
    return render(request, "banka/hesap_list.html", {"hesaplar": hesaplar})


def hesap_ekle(request):
    form = BankaHesabiForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Banka hesabı eklendi.")
        return redirect("banka_hesap_listesi")
    return render(request, "banka/hesap_form.html", {"form": form, "baslik": "Yeni Banka Hesabı"})


def hesap_duzenle(request, pk):
    hesap = get_object_or_404(BankaHesabi, pk=pk)
    form = BankaHesabiForm(request.POST or None, instance=hesap)
    if form.is_valid():
        form.save()
        messages.success(request, "Hesap güncellendi.")
        return redirect("banka_hesap_listesi")
    return render(request, "banka/hesap_form.html", {"form": form, "baslik": "Hesap Düzenle"})


# ── Banka Ekstreleri ─────────────────────────────────────────────────────────

def ekstre_listesi(request):
    ekstreler = BankaEkstre.objects.select_related("banka_hesabi").all()
    return render(request, "banka/ekstre_list.html", {"ekstreler": ekstreler})


def ekstre_yukle(request):
    form = BankaEkstreYukleForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        ekstre = form.save()
        # Parse işlemi başlat
        uzanti = ekstre.dosya_uzantisi
        try:
            satirlar = parse_ekstre(ekstre.dosya.path, uzanti)
            olusturulan = 0
            with transaction.atomic():
                for satir in satirlar:
                    BankaHareketi.objects.create(
                        ekstre=ekstre,
                        banka_hesabi=ekstre.banka_hesabi,
                        islem_tarihi=satir["tarih"],
                        aciklama=satir["aciklama"],
                        tutar=satir["tutar"],
                        tip=satir["tip"],
                    )
                    olusturulan += 1
                ekstre.islendi = True
                ekstre.save(update_fields=["islendi"])
            messages.success(
                request,
                f"Ekstre yüklendi. {olusturulan} işlem satırı otomatik aktarıldı.",
            )
        except Exception as exc:
            messages.warning(request, f"Ekstre yüklendi fakat otomatik parse başarısız: {exc}")
        return redirect("banka_ekstre_listesi")
    return render(request, "banka/ekstre_yukle.html", {"form": form})


def ekstre_detay(request, pk):
    ekstre = get_object_or_404(BankaEkstre, pk=pk)
    hareketler = ekstre.hareketler.select_related("cari").all()
    return render(request, "banka/ekstre_detay.html", {"ekstre": ekstre, "hareketler": hareketler})


# ── Banka Hareketleri ────────────────────────────────────────────────────────

def hareket_listesi(request):
    q = request.GET.get("q", "")
    tip = request.GET.get("tip", "")
    eslesti = request.GET.get("eslesti", "")
    hareketler = BankaHareketi.objects.select_related("banka_hesabi", "cari").all()
    if q:
        hareketler = hareketler.filter(Q(aciklama__icontains=q) | Q(referans_no__icontains=q))
    if tip:
        hareketler = hareketler.filter(tip=tip)
    if eslesti == "1":
        hareketler = hareketler.filter(eslesti=True)
    elif eslesti == "0":
        hareketler = hareketler.filter(eslesti=False)
    return render(request, "banka/hareket_list.html", {
        "hareketler": hareketler, "q": q, "tip": tip, "eslesti": eslesti
    })


def hareket_ekle(request):
    form = BankaHareketiForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Hareket eklendi.")
        return redirect("banka_hareket_listesi")
    return render(request, "banka/hareket_form.html", {"form": form, "baslik": "Yeni Banka Hareketi"})


def hareket_eslestir(request, pk):
    hareket = get_object_or_404(BankaHareketi, pk=pk)
    form = EslestirForm(request.POST or None, instance=hareket)
    if form.is_valid():
        h = form.save(commit=False)
        h.eslesti = bool(h.cari)
        h.save()
        messages.success(request, "Eşleştirme kaydedildi.")
        return redirect("banka_hareket_listesi")
    return render(request, "banka/eslestir_form.html", {"form": form, "hareket": hareket})
