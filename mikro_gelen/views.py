import logging
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import MikroFatura, MikroCariHesap

logger = logging.getLogger("mikro_sync")


@login_required
def fatura_liste(request):
    qs = MikroFatura.objects.select_related("firma_ayar")
    durum = request.GET.get("durum", "")
    firma_id = request.GET.get("firma", "")
    if durum:
        qs = qs.filter(durum=durum)
    if firma_id:
        qs = qs.filter(firma_ayar_id=firma_id)
    return render(request, "mikro_gelen/fatura_liste.html", {"faturalar": qs})


@login_required
def fatura_detay(request, pk):
    fatura = get_object_or_404(MikroFatura, pk=pk)
    return render(request, "mikro_gelen/fatura_detay.html", {"fatura": fatura})
