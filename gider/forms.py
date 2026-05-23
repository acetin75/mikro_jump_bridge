from django import forms
from muhasebe_buro.forms_mixin import BootstrapFormMixin
from .models import Gider, GiderKategori


class GiderForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Gider
        fields = [
            "kategori", "tarih", "aciklama",
            "kdv_haric_tutar", "kdv_orani",
            "belge_no", "odeme_yontemi", "notlar",
        ]
        widgets = {
            "tarih": forms.DateInput(attrs={"type": "date"}),
            "notlar": forms.Textarea(attrs={"rows": 3}),
        }


class GiderKategoriForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = GiderKategori
        fields = ["ad"]
