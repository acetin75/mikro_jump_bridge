from django import forms
from muhasebe_buro.forms_mixin import BootstrapFormMixin
from .models import Urun, StokHareketi


class UrunForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Urun
        fields = [
            "kod", "ad", "birim", "kdv_orani",
            "satis_fiyati", "alis_fiyati", "min_stok",
            "degerleme_yontemi", "aktif", "aciklama",
        ]
        widgets = {
            "aciklama": forms.Textarea(attrs={"rows": 3}),
        }


class StokHareketiForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = StokHareketi
        fields = ["urun", "tarih", "tip", "miktar", "birim_fiyat", "belge_no", "aciklama"]
        widgets = {
            "tarih": forms.DateInput(attrs={"type": "date"}),
            "aciklama": forms.TextInput(),
        }
