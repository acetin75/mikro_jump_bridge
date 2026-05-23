from django import forms
from .models import Sozlesme


class SozlesmeForm(forms.ModelForm):
    class Meta:
        model = Sozlesme
        fields = [
            "cari", "baslik", "sozlesme_no", "durum",
            "baslangic_tarihi", "bitis_tarihi",
            "tutar", "para_birimi", "dosya", "notlar",
        ]
        widgets = {
            "baslangic_tarihi": forms.DateInput(attrs={"type": "date"}),
            "bitis_tarihi": forms.DateInput(attrs={"type": "date"}),
            "notlar": forms.Textarea(attrs={"rows": 3}),
        }
