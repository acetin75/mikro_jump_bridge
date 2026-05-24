from django import forms

from .models import FirmaAyar


class FirmaAyarForm(forms.ModelForm):
    """Firma bağlantı ayarları formu."""

    # Şifre alanları modelde şifreli saklanır, ayrı işlenir
    mikro_sifre_gir = forms.CharField(
        label="Mikro Şifresi",
        widget=forms.PasswordInput(attrs={"class": "form-control", "autocomplete": "new-password"}),
        required=False,
        help_text="Değiştirmek istemiyorsanız boş bırakın.",
    )


    class Meta:
        model = FirmaAyar
        fields = [
            "ad", "aktif", "baglanti_tipi",
            "mikro_sunucu", "mikro_sunucu_vpn", "mikro_sunucu_uzak",
            "mikro_port", "mikro_kullanici",
            "firma_kodu", "calisma_yili", "mikro_api_key",
            "sql_sunucu", "sql_veritabani", "sql_kullanici",
            "notlar",
        ]
        widgets = {
            "ad": forms.TextInput(attrs={"class": "form-control"}),
            "baglanti_tipi": forms.Select(attrs={"class": "form-select"}),
            "mikro_sunucu": forms.TextInput(attrs={"class": "form-control", "placeholder": "192.168.1.10"}),
            "mikro_sunucu_vpn": forms.TextInput(attrs={"class": "form-control", "placeholder": "10.8.0.5"}),
            "mikro_sunucu_uzak": forms.TextInput(attrs={"class": "form-control", "placeholder": "127.0.0.1"}),
            "mikro_port": forms.NumberInput(attrs={"class": "form-control"}),
            "mikro_kullanici": forms.TextInput(attrs={"class": "form-control"}),
            "firma_kodu": forms.TextInput(attrs={"class": "form-control", "placeholder": "MORE"}),
            "calisma_yili": forms.TextInput(attrs={"class": "form-control", "placeholder": "2025"}),
            "mikro_api_key": forms.TextInput(attrs={"class": "form-control", "autocomplete": "off"}),
            "sql_sunucu": forms.TextInput(attrs={"class": "form-control"}),
            "sql_veritabani": forms.TextInput(attrs={"class": "form-control"}),
            "sql_kullanici": forms.TextInput(attrs={"class": "form-control"}),
            "notlar": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "aktif": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
