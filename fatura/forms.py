from django import forms
from django.forms import inlineformset_factory
from .models import Fatura, FaturaKalemi


class FaturaForm(forms.ModelForm):
    class Meta:
        model = Fatura
        fields = ["cari", "tip", "tarih", "vade_tarihi", "aciklama", "notlar", "para_birimi"]
        widgets = {
            "tarih": forms.DateInput(attrs={"type": "date"}),
            "vade_tarihi": forms.DateInput(attrs={"type": "date"}),
            "notlar": forms.Textarea(attrs={"rows": 2}),
        }


class FaturaKalemiForm(forms.ModelForm):
    class Meta:
        model = FaturaKalemi
        fields = ["aciklama", "miktar", "birim", "birim_fiyat", "kdv_orani", "iskonto_oran"]
        widgets = {
            "aciklama": forms.TextInput(attrs={"placeholder": "Hizmet / ürün açıklaması"}),
            "miktar": forms.NumberInput(attrs={"step": "0.001", "min": "0"}),
            "birim_fiyat": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "iskonto_oran": forms.NumberInput(attrs={"step": "0.01", "min": "0", "max": "100"}),
        }


FaturaKalemiFormSet = inlineformset_factory(
    Fatura,
    FaturaKalemi,
    form=FaturaKalemiForm,
    extra=3,
    can_delete=True,
    min_num=1,
    validate_min=True,
)
