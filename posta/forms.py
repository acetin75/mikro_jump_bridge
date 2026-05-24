from django import forms

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
            "gonderen_ad",
            "gonderen_email",
            "aktif",
        ]


class EkstreGonderForm(forms.Form):
    cari_kod = forms.CharField(widget=forms.HiddenInput)
    cari_unvan = forms.CharField(widget=forms.HiddenInput, required=False)
    alici_email = forms.EmailField(
        label="Alıcı E-posta",
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "ornek@sirket.com"}),
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
