# Muhasebe Bürosu — GitHub Copilot Talimatları

## Proje Genel Bakış

**Muhasebe Bürosu CRM**, yerel muhasebe büroları için Django + SQLite tabanlı,
kurulum gerektirmez şekilde çalışan bir masaüstü web uygulamasıdır.
Tarayıcı üzerinden `http://127.0.0.1:8000` adresinden erişilir.

---

## Teknoloji Yığını

| Katman | Teknoloji |
|---|---|
| Backend | Django 5.2, Python 3.10+ |
| Veritabanı | SQLite 3 (`db.sqlite3`) |
| Frontend | Bootstrap 5.3 (CDN), Bootstrap Icons (CDN) |
| PDF | xhtml2pdf 0.2.17 |
| Excel | openpyxl 3.1 |
| Banka Ekstresi Parse | pdfplumber, openpyxl |
| Statik dosya | whitenoise |
| Şablon tag | django-widget-tweaks |
| Linter/Format | ruff |
| Dev profiler | django-debug-toolbar (sadece DEBUG=True) |

---

## Proje Yapısı

```
C:\muhasebe_buro\
├── baslat.bat              ← Tek tıkla başlat (kendi .venv kullanır)
├── olustur_admin.py        ← Admin kullanıcı oluşturma scripti
├── pyproject.toml          ← Ruff ve proje meta konfigürasyonu
├── requirements.txt        ← Üretim bağımlılıkları
├── requirements-dev.txt    ← Geliştirme araçları (ruff, debug-toolbar)
├── db.sqlite3              ← Veritabanı (yedek = bu dosyayı kopyala)
├── logs/
│   ├── hata.log            ← ERROR+ kayıtlar (5 MB × 5 yedek)
│   └── uygulama.log        ← INFO+ kayıtlar (10 MB × 3 yedek)
├── media/                  ← Yüklenen dosyalar
├── static/                 ← Proje statik dosyaları
├── templates/              ← Global şablonlar
│   ├── base.html           ← ANA LAYOUT — tüm sayfalar bunu extend eder
│   ├── confirm_delete.html ← Silme onay şablonu (tüm applar paylaşır)
│   ├── registration/
│   │   └── login.html
│   ├── banka/
│   ├── cari/
│   ├── ceksenet/
│   ├── dashboard/
│   ├── fatura/
│   ├── gider/
│   ├── rapor/
│   ├── sozlesme/
│   └── tahsilat/
├── muhasebe_buro/          ← Django proje paketi
│   ├── settings.py
│   ├── urls.py
│   ├── middleware.py       ← LoginZorunluMiddleware
│   ├── forms_mixin.py      ← BootstrapFormMixin
│   └── wsgi.py
├── cari/                   ← Cari hesaplar + hareketler
├── banka/                  ← Banka hesapları, ekstreler, hareketler
├── sozlesme/               ← Sözleşmeler
├── tahsilat/               ← Tahsilat / ödeme kayıtları
├── fatura/                 ← Fatura + KDV modülü
├── ceksenet/               ← Çek & senet takip
├── gider/                  ← Gider kayıtları
├── stok/                   ← Stok / ürün yönetimi
├── kasa/                   ← Kasa defteri (nakit giriş/çıkış)
├── takvim/                 ← Etkinlik & hatırlatıcılar
├── kullanici/              ← Kullanıcı yönetimi
├── rapor/                  ← Excel export + dönemsel özet (DB modeli YOK)
└── dashboard/              ← Ana panel (DB modeli YOK)
```

---

## Uygulama (App) Standartları

Her Django uygulaması şu dosyaları içermeli:

```
appadi/
├── __init__.py
├── apps.py          ← AppConfig (verbose_name Türkçe)
├── models.py        ← Meta: ordering, verbose_name, verbose_name_plural (Türkçe)
├── forms.py         ← BootstrapFormMixin kullan (muhasebe_buro.forms_mixin)
├── views.py         ← logger = logging.getLogger("muhasebe") ile log kaydı tut
├── urls.py          ← app_name = "appadi" namespace zorunlu
├── admin.py         ← list_display, list_filter, search_fields tanımla
└── migrations/
    └── __init__.py
```

**Rapor ve Dashboard** gibi veritabanı modeli olmayan applar `migrations/` içermez.

---

## Model Yazım Kuralları

```python
class Ornek(models.Model):
    # Alan sırası: PK (otomatik) → FK → CharField → sayısal → tarih → bool → auto
    cari = models.ForeignKey("cari.Cari", on_delete=models.PROTECT, related_name="ornekler")
    ad   = models.CharField("Ekran Adı", max_length=100)  # verbose_name daima Türkçe
    tutar = models.DecimalField("Tutar", max_digits=14, decimal_places=2)
    tarih = models.DateField("Tarih")
    aktif = models.BooleanField("Aktif", default=True)
    olusturuldu = models.DateTimeField(auto_now_add=True)
    guncellendi = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-tarih"]
        verbose_name = "Örnek"
        verbose_name_plural = "Örnekler"

    def __str__(self):
        return f"{self.ad}"
```

- `on_delete=models.PROTECT` — veri kaybını önlemek için varsayılan
- `max_digits=14, decimal_places=2` — para alanları için standart
- `blank=True` — opsiyonel metin alanlar; `null=True` yalnızca non-string alanlarda
- Hesaplanan değerler `@property` olarak tanımlanır, veritabanına yazılmaz

---

## View Yazım Kuralları

```python
import logging
logger = logging.getLogger("muhasebe")

def ornek_goruntu(request):
    try:
        # iş mantığı
        pass
    except Exception as e:
        logger.error("Ornek görünüm hatası: %s", e, exc_info=True)
        messages.error(request, "Bir hata oluştu.")
        return redirect("appadi:list")
```

- Function-based views (FBV) kullanılır — class-based tercih edilmez
- `get_object_or_404` ile nesne al
- Başarılı işlemlerde `messages.success`, hatalarda `messages.error`
- Her kaydetme/silme işleminden sonra `redirect(...)` ile yönlendir (PRG pattern)

---

## Form Yazım Kuralları

```python
from muhasebe_buro.forms_mixin import BootstrapFormMixin

class OrnekForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Ornek
        fields = ["alan1", "alan2", ...]
        widgets = {
            "tarih": forms.DateInput(attrs={"type": "date"}),
            "notlar": forms.Textarea(attrs={"rows": 3}),
        }
```

`BootstrapFormMixin` tüm widget'lara `form-control form-select form-check-input`
sınıflarını otomatik ekler.

---

## URL Yazım Kuralları

```python
# Her urls.py dosyasında app_name zorunlu
app_name = "appadi"

urlpatterns = [
    path("",           views.liste,   name="list"),    # liste daima "list"
    path("ekle/",      views.ekle,    name="ekle"),
    path("<int:pk>/",  views.detay,   name="detay"),
    path("<int:pk>/duzenle/", views.duzenle, name="duzenle"),
    path("<int:pk>/sil/",     views.sil,     name="sil"),
]
```

Şablonlarda referans: `{% url 'appadi:list' %}`, `{% url 'appadi:detay' pk %}`

**İstisna:** `cari`, `banka`, `sozlesme`, `tahsilat` eski applar namespace kullanmaz,
adlar doğrudan: `cari_listesi`, `cari_detay`, `banka_ekstre_listesi` gibi.

---

## Şablon (Template) Standartları

### base.html extend etme
```html
{% extends "base.html" %}
{% block title %}Sayfa Başlığı{% endblock %}
{% block page_title %}Sayfa Başlığı{% endblock %}

{% block content %}
<!-- içerik buraya -->
{% endblock %}
```

### Kart / Liste yapısı
```html
<!-- Filtre / Aksiyon çubuğu -->
<div class="card mb-3">
  <div class="card-body py-3">
    <form class="row g-2 align-items-end" method="get">...</form>
  </div>
</div>

<!-- Tablo -->
<div class="table-responsive">
  <table class="table table-hover align-middle">...</table>
</div>
```

### Form sayfası yapısı
```html
<div class="row justify-content-center">
  <div class="col-lg-8">
    <div class="card">
      <div class="card-body">
        <form method="post">{% csrf_token %}...{{ form.as_p }}</form>
      </div>
    </div>
  </div>
</div>
```

### UI Renk Sistemi (Bootstrap 5 + özel)

| Kullanım | Sınıf |
|---|---|
| Ana aksiyon (kaydet, ekle) | `btn-primary` |
| İptal / geri | `btn-secondary` |
| Tehlikeli (sil, iptal) | `btn-danger` / `btn-outline-danger` |
| Başarı (ödendi, aktif) | `text-success` / `badge bg-success` |
| Uyarı (beklemede, yaklaşan) | `text-warning` / `badge bg-warning text-dark` |
| Hata (gecikmiş, vadesi geçmiş) | `text-danger` / `table-danger` |
| Bilgi | `text-info` |
| Para tutarı | `fw-semibold text-end` (sağa hizalı) |
| Durum badge | `badge bg-{renk} rounded-pill` |

### Dashboard stat kartları
```html
<div class="stat-card" style="background:linear-gradient(135deg,#3b82f6,#6366f1)">
  <div class="d-flex justify-content-between align-items-start">
    <div>
      <div class="opacity-75 small">Etiket</div>
      <div class="fs-2 fw-bold">{{ deger }}</div>
    </div>
    <i class="bi bi-ikon fs-2 opacity-50"></i>
  </div>
</div>
```

### İkon kullanımı
Bootstrap Icons (`bi bi-*`) kullanılır. CDN: base.html'de yüklü.
Sık kullanılanlar:
- `bi-people` — cari  
- `bi-receipt` — fatura  
- `bi-cash-coin` — çek/senet  
- `bi-wallet2` — gider  
- `bi-bar-chart-line` — rapor  
- `bi-bank` — banka  
- `bi-file-earmark-text` — sözleşme  
- `bi-arrow-down-circle` — tahsilat  
- `bi-exclamation-triangle-fill` — uyarı  

---

## Loglama Kuralları

```python
import logging
logger = logging.getLogger("muhasebe")

# Kullanım
logger.debug("Detaylı bilgi: %s", degisken)       # Geliştirme sırasında
logger.info("Fatura oluşturuldu: %s", fatura_no)   # Önemli olaylar
logger.warning("Vade geçti: %s", belge_no)         # Dikkat edilmesi gerekenler
logger.error("Kaydetme hatası", exc_info=True)      # Hatalar (stack trace ile)
```

Log dosyaları: `logs/hata.log` (hata+) ve `logs/uygulama.log` (info+)

---

## Para / Sayı Formatı

- Şablonlarda: `{{ tutar|floatformat:2 }} ₺`
- Model alanı: `DecimalField(max_digits=14, decimal_places=2)`
- Python hesaplama: `from decimal import Decimal` kullan — `float` değil
- KDV oranları: `[(0, "%0"), (1, "%1"), (8, "%8"), (10, "%10"), (20, "%20")]`

---

## Önemli Model Alan İsimleri (Mevcut Applar)

### `cari.Cari`
- `ad` (CharField) — unvan (NOT `unvan`, NOT `name`)
- `tip` (musteri / tedarikci / diger)
- `telefon`, `email`, `adres`, `vergi_no`, `vergi_dairesi`, `notlar`, `aktif`

### `cari.HesapHareketi`
- `cari` (FK), `tarih`, `aciklama`, `hareket_tipi`, `borc`, `alacak`, `belge_no`
- (NOT `tutar` — ayrı `borc` ve `alacak` alanları var)

### `fatura.Fatura`
- `fatura_no`, `cari` (FK), `tip` (satis/alis), `durum` (taslak/kesildi/odendi/iptal)
- `tarih`, `vade_tarihi`, `aciklama`, `para_birimi`
- Properties: `kdv_haric_toplam`, `kdv_toplam`, `genel_toplam`, `kdv_ozeti`, `vadesi_gecti_mi`

### `ceksenet.CekSenet`
- `cari` (FK), `tip` (alınan/verilen), `belge_no`, `tutar`, `vade_tarihi`
- `banka_sube`, `durum` (beklemede/tahsil_edildi/iade/protestolu)

### `gider.Gider`
- `kategori` (FK nullable), `tarih`, `aciklama`, `kdv_haric_tutar`, `kdv_orani`
- `odeme_yontemi`, `belge_no`
- Properties: `kdv_tutari`, `kdv_dahil_tutar`

---

## Güvenlik ve Performans Notları

- `SECRET_KEY` üretimde mutlaka değiştirilmeli
- `DEBUG = False` üretimde
- SQLite yeterli — tek kullanıcı yerel uygulama
- Büyük sorgularda `select_related()` ve `prefetch_related()` kullan
- `django-debug-toolbar` ile SQL sorgularını izle (DEBUG modda aktif)

---

## Yedekleme

```bat
:: Tüm veriyi yedeklemek için sadece bu dosyayı kopyala:
copy db.sqlite3 db_yedek_%date:~6,4%%date:~3,2%%date:~0,2%.sqlite3
```

---

## Yaygın Hatalar ve Çözümleri

| Hata | Neden | Çözüm |
|---|---|---|
| `'WSGIRequest' has no attribute 'user'` | Middleware sırası yanlış | `LoginZorunluMiddleware` `AuthenticationMiddleware`'den sonra olmalı |
| `NoReverseMatch: 'fatura'` | App namespace eksik | `urls.py`'de `app_name = "fatura"` kontrol et |
| `OperationalError: no such table` | Migration çalıştırılmamış | `python manage.py migrate` çalıştır |
| `TemplateSyntaxError` | Import eksik | `{% load widget_tweaks %}` veya `{% load static %}` ekle |
| `decimal.InvalidOperation` | `float` ile DecimalField karıştırma | `Decimal("0")` kullan, `0.0` değil |

---

## Kasa Modülü — Otomatik Hareket Kuralları

`kasa/utils.py` içindeki yardımcılar şu koşullarda otomatik `KasaHareketi` oluşturur:

| Tetikleyici | Koşul | Hareket Tipi |
|---|---|---|
| `tahsilat_ekle` view | `odeme_yontemi == "nakit"` | tahsilat.tip'e göre giriş/çıkış |
| `gider_ekle` view | `odeme_yontemi == "nakit"` | çıkış (kdv_dahil_tutar) |
| `fatura_durum_degistir` | `yeni_durum == "odendi"` + `odeme_yontemi == "nakit"` | fatura.tip'e göre giriş/çıkış |

Otomatik hareketler `KasaHareketi.otomatik_mi == True` olarak işaretlenir — kullanıcı arayüzünden **silinemez**.

---

## Mikro Sync — Ayrı ERP Köprüsü Projesi

`C:\mikro_sync\` — **ayrı Django projesi**, port **8001**'de çalışır.
Mikro ERP ↔ Muhasebe Bürosu iki yönlü senkronizasyon köprüsü.

### Bağlantı Mimarisi

```
C:\muhasebe_buro\   (port 8000)
      ↕  /api/v1/  (Token auth)
C:\mikro_sync\      (port 8001)
      ↕
   Mikro ERP API   (port 8094)
```

### Muhasebe Bürosu REST API Endpoint'leri

`muhasebe_buro/api_views.py` — Token korumalı, DRF gerektirmez.

| Endpoint | Method | Açıklama |
|---|---|---|
| `/api/v1/ping/` | GET | Bağlantı testi |
| `/api/v1/cari/` | GET | Aktif cari listesi (id, ad, vergi_no, tip) |
| `/api/v1/fatura/aktar/` | POST | Alış faturasını kaydet |

**Token ayarı:** `settings.py` → `MIKRO_SYNC_API_TOKEN` (`.env` üzerinden).
Token gönderimi: `Authorization: Token <token>` başlığı.

### fatura/aktar POST body

```json
{
  "fat_guid": "...",
  "cari_id": 5,
  "tarih": "2026-01-15",
  "vade_tarihi": "2026-02-15",
  "fatura_no": "ABC00001",
  "aciklama": "...",
  "satirlar": [
    {"ad": "...", "miktar": 1, "birim_fiyat": "...", "kdv_orani": 20, "tutar": "..."}
  ]
}
```

Tekrar gönderimde `{"durum": "mevcut", "fatura_id": N}` döner (idempotent).

### mikro_sync Uygulama Yapısı

```
C:\mikro_sync\
├── sync_motor/
│   ├── models.py    ← FirmaAyar, CariEslestirme, StokEslestirme, ImportLog
│   ├── client.py    ← MikroApiClient, MuhasebeBuroClient
│   ├── matcher.py   ← Kural tabanlı öğrenen eşleştirme motoru
│   ├── importer.py  ← 5 adımlı aktarım pipeline (MikroImporter)
│   └── views.py     ← Firma yönetimi, import başlat, onay ekranı
└── mikro_gelen/
    └── models.py    ← MikroFatura, MikroCariHesap, MikroStokKarti (staging)
```

### Şifre Güvenliği (FirmaAyar)

Mikro şifreleri DB'de `django.core.signing.Signer` ile şifreli saklanır:
```python
firma.sifre_kaydet("sifre")   # şifreler ve kaydeder
firma.sifre_al()               # çözer ve döndürür
```
Ham şifre asla `_mikro_sifre_sifreli` alanına yazılmaz.
