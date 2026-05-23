from django import forms
from muhasebe_buro.forms_mixin import BootstrapFormMixin
from .models import CekSenet


class CekSenetForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = CekSenet
        fields = [
            "cari", "tip", "belge_no", "tutar",
            "vade_tarihi", "kesildi_tarihi", "banka_sube", "durum", "notlar",
        ]
        widgets = {
            "vade_tarihi": forms.DateInput(attrs={"type": "date"}),
            "kesildi_tarihi": forms.DateInput(attrs={"type": "date"}),
            "notlar": forms.Textarea(attrs={"rows": 3}),
        }
