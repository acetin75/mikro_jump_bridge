from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password

from mikro_sync.forms_mixin import BootstrapFormMixin


class KullaniciEkleForm(BootstrapFormMixin, forms.Form):
    kullanici_adi = forms.CharField(
        label="Kullanıcı Adı",
        max_length=150,
        help_text="Giriş yaparken kullanılacak ad. Boşluk ve Türkçe karakter kullanmayın.",
    )
    ad_soyad = forms.CharField(
        label="Ad Soyad",
        max_length=200,
        required=False,
    )
    email = forms.EmailField(
        label="E-posta",
        required=False,
    )
    sifre = forms.CharField(
        label="Şifre",
        widget=forms.PasswordInput,
    )
    sifre_tekrar = forms.CharField(
        label="Şifre Tekrar",
        widget=forms.PasswordInput,
    )
    yonetici = forms.BooleanField(
        label="Yönetici Yetkisi",
        required=False,
        help_text="İşaretlenirse kullanıcı tüm sayfalara erişebilir ve kullanıcı ekleyebilir.",
    )

    def clean_kullanici_adi(self):
        ad = self.cleaned_data["kullanici_adi"]
        if User.objects.filter(username=ad).exists():
            raise forms.ValidationError("Bu kullanıcı adı zaten kullanılıyor.")
        return ad

    def clean_sifre(self):
        sifre = self.cleaned_data.get("sifre")
        if sifre:
            validate_password(sifre)
        return sifre

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("sifre") and cleaned.get("sifre_tekrar"):
            if cleaned["sifre"] != cleaned["sifre_tekrar"]:
                self.add_error("sifre_tekrar", "Şifreler eşleşmiyor.")
        return cleaned


class SifreDegistirForm(BootstrapFormMixin, forms.Form):
    yeni_sifre = forms.CharField(
        label="Yeni Şifre",
        widget=forms.PasswordInput,
    )
    yeni_sifre_tekrar = forms.CharField(
        label="Yeni Şifre Tekrar",
        widget=forms.PasswordInput,
    )

    def clean_yeni_sifre(self):
        sifre = self.cleaned_data.get("yeni_sifre")
        if sifre:
            validate_password(sifre)
        return sifre

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("yeni_sifre") and cleaned.get("yeni_sifre_tekrar"):
            if cleaned["yeni_sifre"] != cleaned["yeni_sifre_tekrar"]:
                self.add_error("yeni_sifre_tekrar", "Şifreler eşleşmiyor.")
        return cleaned
