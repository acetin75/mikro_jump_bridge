from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

from mikro_sync.forms_mixin import BootstrapFormMixin

from .models import MailAyar


class MailAyarForm(BootstrapFormMixin, forms.ModelForm):
    sifre = forms.CharField(
        label="Uygulama Şifresi / SMTP Şifresi",
        widget=forms.PasswordInput(render_value=False),
        required=False,
        help_text="Boş bırakılırsa mevcut şifre korunur.",
    )

    class Meta:
        model = MailAyar
        fields = [
            "smtp_sunucu",
            "smtp_port",
            "kullanici",
            "tls_kullan",
            "tls_dogrulamayi_atla",
            "gonderen_ad",
            "gonderen_email",
            "aktif",
        ]


def _email_listesi_dogrula(deger: str) -> list[str]:
    """Virgülle ayrılmış e-posta listesini doğrulayıp döndürür."""
    adresler = [e.strip() for e in deger.split(",") if e.strip()]
    for adres in adresler:
        try:
            validate_email(adres)
        except ValidationError:
            raise ValidationError(f"Geçersiz e-posta adresi: {adres}")
    return adresler


class EkstreGonderForm(forms.Form):
    cari_kod = forms.CharField(widget=forms.HiddenInput)
    cari_unvan = forms.CharField(widget=forms.HiddenInput, required=False)
    alici_email = forms.CharField(
        label="Alıcı (TO)",
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "ornek@firma.com, diger@firma.com"}
        ),
        help_text="Birden fazla adres için virgülle ayırın.",
    )
    bilgi_email = forms.CharField(
        label="Bilgi (CC)",
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "ali@sirket.com, mehmet@sirket.com"}
        ),
        help_text="Şirket içi kişilere bilgi için virgülle ayırın. Boş bırakılabilir.",
    )
    donem_baslangic = forms.DateField(
        label="Dönem Başlangıcı",
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
    )
    donem_bitis = forms.DateField(
        label="Dönem Bitişi",
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
    )
    konu = forms.CharField(
        label="Konu (opsiyonel)",
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Boş bırakılırsa otomatik oluşturulur"}
        ),
    )

    def clean_alici_email(self):
        return _email_listesi_dogrula(self.cleaned_data.get("alici_email", ""))

    def clean_bilgi_email(self):
        val = self.cleaned_data.get("bilgi_email", "")
        return _email_listesi_dogrula(val) if val.strip() else []
