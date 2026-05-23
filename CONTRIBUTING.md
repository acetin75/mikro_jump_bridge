# Katkıda Bulunma Kılavuzu

Muhasebe Bürosu CRM projesine katkıda bulunmak istediğiniz için teşekkürler!

---

## Başlamadan Önce

1. Projeyi fork'layın
2. Kendi branch'inizi oluşturun: `git checkout -b ozellik/yeni-modul`
3. Değişikliklerinizi yapın
4. Testleri çalıştırın: `python manage.py check`
5. Pull Request gönderin

---

## Geliştirme Ortamı

```bat
:: Repoyu klonlayın
git clone https://github.com/KULLANICI/muhasebe-buro.git
cd muhasebe-buro

:: Ortam değişkenlerini ayarlayın
copy .env.example .env

:: Uygulamayı başlatın
baslat.bat
```

---

## Kod Standartları

- **Python:** ruff ile lint ve format zorunlu
  ```bat
  .venv\Scripts\ruff check .
  .venv\Scripts\ruff format .
  ```
- **View:** Function-based views (FBV), class-based tercih edilmez
- **Model:** `verbose_name` Türkçe olmalı, `on_delete=models.PROTECT` varsayılan
- **Form:** `BootstrapFormMixin` kullanılmalı
- **URL:** `app_name` namespace zorunlu (eski applar hariç: cari, banka, sozlesme, tahsilat)
- **Log:** `logger = logging.getLogger("muhasebe")` kullan

---

## Pull Request Kuralları

- Her PR tek bir özellik veya hata düzeltmesi içermelidir
- Commit mesajları Türkçe veya İngilizce olabilir
- Migration dosyaları PR'a dahil edilmelidir
- `python manage.py check` sıfır hata döndürmelidir

---

## Hata Bildirme

GitHub Issues üzerinden bildirin. Lütfen şunları ekleyin:
- Django ve Python sürümü
- Hatanın nasıl oluştuğu (adım adım)
- Beklenen ve gerçekleşen davranış
- `logs/hata.log` dosyasından ilgili satırlar

---

## Lisans

Katkılarınız [MIT Lisansı](LICENSE) kapsamında yayınlanacaktır.
