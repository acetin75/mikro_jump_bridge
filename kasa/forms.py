from django import forms
from muhasebe_buro.forms_mixin import BootstrapFormMixin
from .models import KasaHesabi, KasaHareketi


class KasaHesabiForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = KasaHesabi
        fields = ["ad", "para_birimi", "acilis_bakiyesi", "aktif", "aciklama"]


class KasaHareketiForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = KasaHareketi
        fields = ["kasa", "tarih", "tip", "tutar", "aciklama", "belge_no"]
        widgets = {
            "tarih": forms.DateInput(attrs={"type": "date"}),
        }
