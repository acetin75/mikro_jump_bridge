from django import forms
from .models import Cari, HesapHareketi


class CariForm(forms.ModelForm):
    class Meta:
        model = Cari
        fields = ["ad", "tip", "vergi_no", "vergi_dairesi", "telefon", "email", "adres", "notlar", "aktif"]
        widgets = {
            "adres": forms.Textarea(attrs={"rows": 3}),
            "notlar": forms.Textarea(attrs={"rows": 3}),
        }


class HesapHareketiForm(forms.ModelForm):
    class Meta:
        model = HesapHareketi
        fields = ["cari", "tarih", "belge_no", "aciklama", "hareket_tipi", "borc", "alacak", "para_birimi"]
        widgets = {
            "tarih": forms.DateInput(attrs={"type": "date"}),
        }


class HesapHareketiCariForm(forms.ModelForm):
    """Belirli bir cari için hareket formu — cari alanı gizli."""

    class Meta:
        model = HesapHareketi
        fields = ["tarih", "belge_no", "aciklama", "hareket_tipi", "borc", "alacak", "para_birimi"]
        widgets = {
            "tarih": forms.DateInput(attrs={"type": "date"}),
        }
