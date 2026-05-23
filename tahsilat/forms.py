from django import forms
from .models import Tahsilat


class TahsilatForm(forms.ModelForm):
    class Meta:
        model = Tahsilat
        fields = ["cari", "tip", "tarih", "tutar", "para_birimi", "odeme_yontemi", "aciklama", "belge_no"]
        widgets = {
            "tarih": forms.DateInput(attrs={"type": "date"}),
        }
