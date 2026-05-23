import io
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db import transaction
from django.db.models import Q, Sum
from django.http import HttpResponse
from django.template.loader import get_template
from django.utils import timezone
from .models import Fatura, FaturaKalemi, KDV_ORANLARI
from .forms import FaturaForm, FaturaKalemiFormSet
from cari.models import HesapHareketi
from kasa.utils import fatura_kasa_hareketi_olustur


# ── Liste & Detay ────────────────────────────────────────────────────────────

def fatura_listesi(request):
    q = request.GET.get("q", "")
    tip = request.GET.get("tip", "")
    durum = request.GET.get("durum", "")
    faturalar = Fatura.objects.select_related("cari").prefetch_related("kalemler")
    if q:
        faturalar = faturalar.filter(
            Q(fatura_no__icontains=q) | Q(cari__ad__icontains=q) | Q(aciklama__icontains=q)
        )
    if tip:
        faturalar = faturalar.filter(tip=tip)
    if durum:
        faturalar = faturalar.filter(durum=durum)
    return render(request, "fatura/list.html", {
        "faturalar": faturalar, "q": q, "tip": tip, "durum": durum
    })


def fatura_detay(request, pk):
    fatura = get_object_or_404(
        Fatura.objects.select_related("cari").prefetch_related("kalemler"), pk=pk
    )
    return render(request, "fatura/detail.html", {"fatura": fatura})


# ── Oluştur / Düzenle ────────────────────────────────────────────────────────

def fatura_ekle(request):
    if request.method == "POST":
        form = FaturaForm(request.POST)
        formset = FaturaKalemiFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                fatura = form.save()
                formset.instance = fatura
                formset.save()
                _cari_hareket_ekle(fatura)
            messages.success(request, f"Fatura {fatura.fatura_no} oluşturuldu.")
            return redirect("fatura_detay", pk=fatura.pk)
    else:
        form = FaturaForm()
        formset = FaturaKalemiFormSet()
    return render(request, "fatura/form.html", {
        "form": form, "formset": formset, "baslik": "Yeni Fatura"
    })


def fatura_duzenle(request, pk):
    fatura = get_object_or_404(Fatura, pk=pk)
    if request.method == "POST":
        form = FaturaForm(request.POST, instance=fatura)
        formset = FaturaKalemiFormSet(request.POST, instance=fatura)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, "Fatura güncellendi.")
            return redirect("fatura_detay", pk=pk)
    else:
        form = FaturaForm(instance=fatura)
        formset = FaturaKalemiFormSet(instance=fatura)
    return render(request, "fatura/form.html", {
        "form": form, "formset": formset, "baslik": "Fatura Düzenle", "fatura": fatura
    })


def fatura_durum_degistir(request, pk):
    fatura = get_object_or_404(Fatura, pk=pk)
    yeni_durum = request.POST.get("durum")
    if yeni_durum in dict(Fatura.DURUM):
        with transaction.atomic():
            fatura.durum = yeni_durum
            fatura.save(update_fields=["durum"])
            # Nakit ödendi → kasa hareketi
            if yeni_durum == "odendi":
                fatura_kasa_hareketi_olustur(fatura)
        messages.success(request, f"Durum '{fatura.get_durum_display()}' olarak güncellendi.")
    return redirect("fatura_detay", pk=pk)


# ── PDF Yazdır ───────────────────────────────────────────────────────────────

def _qr_base64(fatura):
    """E-arşiv QR içeriği: fatura_no|uuid|tutar|tarih → base64 PNG."""
    try:
        import qrcode
        import base64
        icerik = (
            f"FATURA_NO:{fatura.fatura_no}\n"
            f"UUID:{fatura.e_fatura_uuid}\n"
            f"TUTAR:{fatura.genel_toplam}\n"
            f"TARIH:{fatura.tarih}"
        )
        qr = qrcode.QRCode(version=1, box_size=4, border=2)
        qr.add_data(icerik)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()
    except Exception:
        return ""


def fatura_pdf(request, pk):
    fatura = get_object_or_404(
        Fatura.objects.select_related("cari").prefetch_related("kalemler"), pk=pk
    )
    try:
        from xhtml2pdf import pisa

        qr_b64 = _qr_base64(fatura) if fatura.tip == "satis" else ""
        template = get_template("fatura/print.html")
        html = template.render({"fatura": fatura, "request": request, "qr_b64": qr_b64})
        buffer = io.BytesIO()
        pisa_status = pisa.CreatePDF(html, dest=buffer)
        if pisa_status.err:
            raise Exception("PDF oluşturma hatası")
        buffer.seek(0)
        response = HttpResponse(buffer, content_type="application/pdf")
        response["Content-Disposition"] = (
            f'attachment; filename="fatura_{fatura.fatura_no}.pdf"'
        )
        return response
    except ImportError:
        # xhtml2pdf yoksa print sayfasına yönlendir
        messages.warning(request, "PDF modülü yüklü değil. Tarayıcınızdan Ctrl+P ile yazdırabilirsiniz.")
        return redirect("fatura_yazdir", pk=pk)


def fatura_yazdir(request, pk):
    """Tarayıcı baskı diyaloğu için print-optimized HTML."""
    fatura = get_object_or_404(
        Fatura.objects.select_related("cari").prefetch_related("kalemler"), pk=pk
    )
    qr_b64 = _qr_base64(fatura) if fatura.tip == "satis" else ""
    return render(request, "fatura/print.html", {"fatura": fatura, "qr_b64": qr_b64})


# ── KDV Özeti ────────────────────────────────────────────────────────────────

def kdv_ozet(request):
    ay = request.GET.get("ay", timezone.now().strftime("%Y-%m"))
    try:
        yil, mon = int(ay.split("-")[0]), int(ay.split("-")[1])
    except (ValueError, IndexError):
        yil, mon = timezone.now().year, timezone.now().month

    satis_faturalari = Fatura.objects.filter(
        tip="satis", tarih__year=yil, tarih__month=mon
    ).exclude(durum="iptal").prefetch_related("kalemler")

    alis_faturalari = Fatura.objects.filter(
        tip="alis", tarih__year=yil, tarih__month=mon
    ).exclude(durum="iptal").prefetch_related("kalemler")

    # KDV oranlara göre topla
    def kdv_topla(faturalar):
        sonuc = {oran: {"matrah": 0, "kdv": 0} for oran, _ in KDV_ORANLARI}
        for f in faturalar:
            for oran, veriler in f.kdv_ozeti.items():
                if oran not in sonuc:
                    sonuc[oran] = {"matrah": 0, "kdv": 0}
                sonuc[oran]["matrah"] += veriler["matrah"]
                sonuc[oran]["kdv"] += veriler["kdv"]
        return {k: v for k, v in sonuc.items() if v["kdv"] > 0 or v["matrah"] > 0}

    satis_kdv = kdv_topla(satis_faturalari)
    alis_kdv = kdv_topla(alis_faturalari)

    tahsil_edilen_kdv = sum(v["kdv"] for v in satis_kdv.values())
    odenen_kdv = sum(v["kdv"] for v in alis_kdv.values())
    odenmesi_gereken = tahsil_edilen_kdv - odenen_kdv

    return render(request, "fatura/kdv_ozet.html", {
        "ay": ay, "yil": yil, "mon": mon,
        "satis_kdv": satis_kdv,
        "alis_kdv": alis_kdv,
        "tahsil_edilen_kdv": tahsil_edilen_kdv,
        "odenen_kdv": odenen_kdv,
        "odenmesi_gereken": odenmesi_gereken,
        "satis_faturalari": satis_faturalari,
        "alis_faturalari": alis_faturalari,
    })


# ── Yardımcı ────────────────────────────────────────────────────────────────

def _cari_hareket_ekle(fatura: Fatura):
    """Fatura kaydedilince cari hesap hareketine otomatik işle."""
    if fatura.durum in ("taslak", "iptal"):
        return
    toplam = fatura.genel_toplam
    HesapHareketi.objects.create(
        cari=fatura.cari,
        tarih=fatura.tarih,
        belge_no=fatura.fatura_no,
        aciklama=fatura.aciklama or f"{fatura.get_tip_display()} faturası",
        hareket_tipi="fatura",
        borc=toplam if fatura.tip == "satis" else 0,
        alacak=toplam if fatura.tip == "alis" else 0,
        para_birimi=fatura.para_birimi,
    )


def fatura_xml_indir(request, pk):
    """UBL-TR 2.1 formatında e-fatura XML dosyası indir."""
    fatura = get_object_or_404(Fatura, pk=pk)
    try:
        from .efatura import ubl_xml_uret
        xml_bytes = ubl_xml_uret(fatura)
        dosya_adi = f"efatura_{fatura.fatura_no}.xml"
        # E-fatura durumunu güncelle
        if fatura.e_fatura_durum == "yok":
            fatura.e_fatura_durum = "hazir"
            fatura.save(update_fields=["e_fatura_durum"])
        from django.http import HttpResponse
        response = HttpResponse(xml_bytes, content_type="application/xml; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="{dosya_adi}"'
        logger.info("E-fatura XML indirildi: %s", fatura.fatura_no)
        return response
    except Exception as e:
        logger.error("E-fatura XML üretme hatası: %s", e, exc_info=True)
        messages.error(request, f"XML üretilirken hata oluştu: {e}")
        return redirect("fatura_detay", pk=pk)
