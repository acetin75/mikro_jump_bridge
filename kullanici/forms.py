from django import forms
from django.contrib.auth.models import Group, User

from muhasebe_buro.forms_mixin import BootstrapFormMixin


class KullaniciForm(BootstrapFormMixin, forms.ModelForm):
    rol = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        required=False,
        label="Rol",
        empty_label="— Rol Yok (Görüntüleyici) —",
    )
    sifre = forms.CharField(
        label="Şifre",
        required=False,
        widget=forms.PasswordInput(attrs={"placeholder": "Boş bırakılırsa değişmez"}),
        help_text="Yeni kullanıcı için zorunlu. Düzenlemede boş bırakılabilir.",
    )

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "is_active"]
        labels = {
            "username": "Kullanıcı Adı",
            "first_name": "Ad",
            "last_name": "Soyad",
            "email": "E-posta",
            "is_active": "Aktif",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Mevcut kullanıcının rolünü göster
        if self.instance.pk:
            grup = self.instance.groups.first()
            if grup:
                self.fields["rol"].initial = grup

    def save(self, commit=True):
        user = super().save(commit=False)
        sifre = self.cleaned_data.get("sifre")
        if sifre:
            user.set_password(sifre)
        if commit:
            user.save()
            # Grup güncelle
            user.groups.clear()
            rol = self.cleaned_data.get("rol")
            if rol:
                user.groups.add(rol)
        return user
