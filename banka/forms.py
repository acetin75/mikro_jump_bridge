from django import forms
from .models import BankaHesabi, BankaEkstre, BankaHareketi


class BankaHesabiForm(forms.ModelForm):
    class Meta:
        model = BankaHesabi
        fields = ["ad", "banka_adi", "sube", "hesap_no", "para_birimi", "aktif"]


class BankaEkstreYukleForm(forms.ModelForm):
    class Meta:
        model = BankaEkstre
        fields = ["banka_hesabi", "dosya", "donem_baslangic", "donem_bitis", "notlar"]
        widgets = {
            "donem_baslangic": forms.DateInput(attrs={"type": "date"}),
            "donem_bitis": forms.DateInput(attrs={"type": "date"}),
            "notlar": forms.Textarea(attrs={"rows": 2}),
        }

    def clean_dosya(self):
        dosya = self.cleaned_data.get("dosya")
        if dosya:
            uzanti = dosya.name.rsplit(".", 1)[-1].lower()
            if uzanti not in ("xlsx", "xls", "pdf"):
                raise forms.ValidationError("Sadece Excel (.xlsx, .xls) veya PDF dosyası yüklenebilir.")
        return dosya


class BankaHareketiForm(forms.ModelForm):
    class Meta:
        model = BankaHareketi
        fields = ["banka_hesabi", "islem_tarihi", "aciklama", "tutar", "tip", "referans_no", "cari"]
        widgets = {
            "islem_tarihi": forms.DateInput(attrs={"type": "date"}),
        }


class EslestirForm(forms.ModelForm):
    class Meta:
        model = BankaHareketi
        fields = ["cari", "eslesti"]
