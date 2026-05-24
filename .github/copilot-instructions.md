# Mikro Jump Bridge — GitHub Copilot Talimatları

> Bu dosya yaşayan bir standarttır. Kural eklenince güncellenir; kural çiğnenince hata sayılır.
> Tüm detaylı gerekçeler → `docs/runbooks/`

## Proje Genel Bakış

**Mikro Jump Bridge** (`C:\mikro_jump_bridge`), Mikro ERP'yi doğrudan sorgulayan,
çok firmalı cari hesap yönetimi ve iki yönlü senkronizasyon köprüsüdür.
Django + SQLite tabanlı, kurulum gerektirmez şekilde çalışır.
Tarayıcı üzerinden `http://127.0.0.1:8001` adresinden erişilir.
GitHub: `acetin75/mikro_jump_bridge` — Django paket adı `mikro_sync` (içsel).

---

## Teknoloji Yığını

| Katman | Teknoloji |
|---|---|
| Backend | Django 5.2, Python 3.10+ |
| Veritabanı | SQLite 3 (`db.sqlite3`) |
| Frontend | Bootstrap 5.3 (CDN), Bootstrap Icons (CDN) |
| HTTP İstemcisi | requests 2.32 |
| XML Güvenliği | defusedxml 0.7 |
| Statik dosya | whitenoise |
| Şablon tag | django-widget-tweaks |
| Env yönetimi | python-decouple (`.env` dosyası) |
| Linter/Format | ruff |

---

## Bağlantı Mimarisi

```
Mikro ERP API  (port 8094)
      ↕  MikroApiClient  (MD5 günlük hash auth)
mikro_gelen/   (staging — ham veriler)
      ↕
hesap_yonetimi/   (okuma amacıyla sorgulama)
```

---

## Proje Yapısı

### Markdown Dosya Konumu Kuralı

- Standart dışı `.md` dosyaları → `docs/` altına konur
- **İstisna:** `README.md`, `CONTRIBUTING.md`, `CHANGELOG.md` — GitHub konvansiyonu gereği **kök dizinde** kalır

```
C:\mikro_jump_bridge\
├── baslat.bat              ← Tek tıkla başlat (venv oluşturur, paket kurar, migrate eder)
├── kontrol.bat             ← Kod kalitesi: ruff+vulture+pip-audit+django check
├── olustur_admin.py        ← Admin kullanıcı oluşturma (interaktif)
├── pyproject.toml          ← Ruff + Vulture konfigürasyonu
├── requirements.txt        ← Üretim bağımlılıkları (tam sürüm ==)
├── requirements-dev.txt    ← Geliştirme araçları (ruff, vulture, pip-audit)
├── db.sqlite3              ← Veritabanı (yedek = bu dosyayı kopyala)
├── docs/runbooks/          ← Geliştirme standartları (01-18 arası runbook)
├── logs/
│   └── mikro_sync.log      ← INFO+ kayıtlar (10 MB × 3 yedek)
├── templates/
│   ├── base.html           ← ANA LAYOUT
│   ├── registration/
│   │   └── login.html
│   ├── sync_motor/         ← Firma, import, onay şablonları
│   ├── mikro_gelen/        ← Staging fatura listeleri
│   └── hesap_yonetimi/     ← Cari sorgulama şablonları
├── mikro_sync/             ← Django proje paketi (paket adı)
│   ├── settings.py         ← python-decouple, fail-fast SECRET_KEY, prod güvenlik bloğu
│   ├── urls.py
│   ├── middleware.py       ← LoginZorunluMiddleware
│   ├── forms_mixin.py      ← BootstrapFormMixin
│   └── wsgi.py
├── sync_motor/             ← ANA UYGULAMA — firma yönetimi + import pipeline
│   ├── models.py           ← FirmaAyar, ImportLog
│   ├── client.py           ← MikroApiClient (sql_oku dahil)
│   ├── forms.py
│   ├── views.py
│   └── urls.py
├── mikro_gelen/            ← STAGING ALANI — Mikro'dan gelen ham veriler
│   ├── models.py           ← MikroFatura, MikroCariHesap, MikroStokKarti
│   ├── views.py
│   └── urls.py
└── hesap_yonetimi/         ← CARİ SORGULAMA — okuma amaçlı (DB'ye yazmaz)
    ├── views.py            ← panel, firma_kartlari, hesap_hareketleri, bakiye_raporu
    └── urls.py
    └── urls.py
```

---

## Uygulama (App) Standartları

Her Django uygulaması şu dosyaları içermeli:

```
appadi/
├── __init__.py
├── apps.py          ← AppConfig (verbose_name Türkçe)
├── models.py        ← Meta: ordering, verbose_name, verbose_name_plural (Türkçe)
├── forms.py         ← BootstrapFormMixin kullan (mikro_sync.forms_mixin)
├── views.py         ← logger = logging.getLogger("mikro_sync") ile log kaydı tut
├── urls.py          ← app_name namespace YOK — doğrudan isimler kullanılır
├── admin.py         ← list_display, list_filter, search_fields tanımla
└── migrations/
```

---

## Model Yazım Kuralları

```python
class Ornek(models.Model):
    # Alan sırası: PK (otomatik) → FK → CharField → sayısal → tarih → bool → auto
    firma_ayar = models.ForeignKey("sync_motor.FirmaAyar", on_delete=models.PROTECT)
    ad          = models.CharField("Açıklama", max_length=200)  # verbose_name Türkçe
    tutar       = models.DecimalField("Tutar", max_digits=14, decimal_places=2)
    tarih       = models.DateField("Tarih")
    durum       = models.CharField("Durum", max_length=20, choices=DURUM, default="ham")
    olusturuldu = models.DateTimeField(auto_now_add=True)
    guncellendi = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-olusturuldu"]
        verbose_name = "Örnek"
        verbose_name_plural = "Örnekler"
```

- `on_delete=models.PROTECT` — veri kaybını önlemek için varsayılan
- `max_digits=14, decimal_places=2` — para alanları için standart
- Şifreli alanlar: `django.core.signing.Signer` kullan, ham değer asla DB'ye yazılmaz
- Hesaplanan değerler `@property` olarak tanımlanır

---

## View Yazım Kuralları

```python
import logging
logger = logging.getLogger("mikro_sync")

@login_required
def ornek_goruntu(request):
    try:
        # iş mantığı
        pass
    except Exception as e:
        logger.error("Hata: %s", e, exc_info=True)
        messages.error(request, "Bir hata oluştu.")
        return redirect("anasayfa")
```

- Function-based views (FBV) — class-based tercih edilmez
- `@login_required` dekoratörü zorunlu (LoginZorunluMiddleware zaten tüm sayfaları korur)
- `get_object_or_404` ile nesne al
- Başarılı işlemlerde `messages.success`, hatalarda `messages.error`
- Her kaydetme/silmeden sonra `redirect(...)` (PRG pattern)

---

## Form Yazım Kuralları

```python
from mikro_sync.forms_mixin import BootstrapFormMixin

class OrnekForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Ornek
        fields = ["alan1", "alan2"]
        widgets = {
            "tarih": forms.DateInput(attrs={"type": "date"}),
        }
```

---

## URL Yazım Kuralları

`app_name` namespace **kullanılmaz** — doğrudan isimler:

```python
urlpatterns = [
    path("",                          views.anasayfa,      name="anasayfa"),
    path("firmalar/",                 views.firma_liste,   name="firma_liste"),
    path("firmalar/ekle/",            views.firma_ekle,    name="firma_ekle"),
    path("firmalar/<int:pk>/duzenle/",views.firma_duzenle, name="firma_duzenle"),
    path("importlar/",                views.import_liste,  name="import_liste"),
    path("import/<int:pk>/baslat/",   views.import_baslat, name="import_baslat"),
]
```

Şablonlarda: `{% url 'firma_liste' %}`, `{% url 'firma_duzenle' pk %}`

---

## Şablon Standartları

```html
{% extends "base.html" %}
{% block title %}Sayfa Başlığı{% endblock %}
{% block page_title %}Sayfa Başlığı{% endblock %}
{% block content %}
<!-- içerik -->
{% endblock %}
```

---

## Loglama Kuralları

```python
import logging
logger = logging.getLogger("mikro_sync")

logger.debug("API isteği: %s", endpoint)
logger.info("Import tamamlandı: %s fatura aktarıldı", adet)
logger.warning("Eşleştirme bulunamadı: %s", mikro_cari_kod)
logger.error("Aktarım hatası: %s", e, exc_info=True)
```

Log dosyası: `logs/mikro_sync.log` (INFO+, 10 MB × 3 yedek)

---

## Önemli Model Alanları

### `sync_motor.FirmaAyar`
- `ad`, `aktif`, `baglanti_tipi` (api/sql/manuel)
- `mikro_sunucu`, `mikro_port` (8094), `mikro_kullanici`, `firma_kodu`, `calisma_yili`
- `_mikro_sifre_sifreli` — **doğrudan yazma!** `firma.sifre_kaydet("sifre")` kullan
- `firma.api_url` → `http://{sunucu}:{port}/Api/APIMethods`

### `sync_motor.ImportLog`
- `firma_ayar` (FK)
- `durum` (beklemede/isleniyor/tamamlandi/kismi/hata/iptal)
- `cekilen_adet`, `aktarilan_adet`, `hata_adet`
- Property: `basari_yuzdesi`

### `mikro_gelen.MikroFatura`
- `fat_guid` (unique), `fat_evrak_seri`, `fat_evrak_sira`, `fat_tarih`
- `fat_cari_kod`, `fat_cari_unvan`, `fat_cari_vkn`
- `durum` (ham/islendi/hata/atla)
- `ham_json` — Mikro API'den gelen orijinal veri, **asla değiştirme**
- Property: `ham_veri` — `ham_json`'u dict döndürür

---

## MikroApiClient Kullanımı

```python
from sync_motor.client import MikroApiClient

client = MikroApiClient(firma_ayar)
# Bağlantı testi
saglik = client.saglik_kontrol()   # {"durum": "ok"} veya exception

# Fatura çekme
faturalar = client.gelen_faturalar(date(2026, 1, 1), date(2026, 1, 31))
```

**Auth:** Her istekte `MD5("YYYY-MM-DD " + sifre)` hash gönderilir — şifre hiçbir
zaman açık metin olarak iletilmez.

---

## Şifre Güvenliği

```python
# KAYDETME — doğru
firma.sifre_kaydet("mikro_sifre")
firma.save()

# OKUMA — doğru
sifre = firma.sifre_al()

# YANLIŞ — asla yapma
firma._mikro_sifre_sifreli = "ham_sifre"  # ← ham değer yazılamaz
```

`django.core.signing.Signer` kullanılır. Ham şifre DB'ye asla yazılmaz.

---

## Güvenlik ve Ortam Değişkenleri

`.env` dosyası (proje kökünde, `.gitignore`'da):
```
SECRET_KEY=guclu-uretilmis-anahtar
DEBUG=False
ALLOWED_HOSTS=127.0.0.1,localhost

# Django admin hesabı — olustur_admin.py bu değerleri okur
ADMIN_KULLANICI=admin
ADMIN_SIFRE=Admin123!.@
```

- `SECRET_KEY` değeri `django-insecure-` ile başlıyorsa ve `DEBUG=False` ise uygulama **başlamaz**
- `DEBUG=True` geliştirme içindir, üretimde `False`
- `ADMIN_SIFRE` tanımlıysa `baslat.bat` admin hesabını **sessizce** oluşturur — interaktif sormaz

### Şifre Kasası — SIFRELER.md

Tüm kimlik bilgileri `SIFRELER.md` dosyasında saklanır:

```
SIFRELER.md       ← Admin şifresi, Mikro bağlantıları, MB API token
.env              ← SECRET_KEY, DEBUG, ADMIN_KULLANICI, ADMIN_SIFRE
```

Her iki dosya da `.gitignore`'dadır — Git'e **asla** gönderilmez.
Yedek alırken `db.sqlite3` + `.env` + `SIFRELER.md` üçlüsünü birlikte kopyala.

**Şifre güncelleme:** `.env` → `ADMIN_SIFRE` değiştir + `SIFRELER.md` güncelle → `baslat.bat` çalıştır.

---

## Para / Sayı Formatı

- Model alanı: `DecimalField(max_digits=14, decimal_places=2)`
- Python hesaplama: `from decimal import Decimal` kullan — `float` değil
- Şablonlarda: `{{ tutar|floatformat:2 }} ₺`

---

## Yedekleme

```bat
copy db.sqlite3 db_yedek_%date:~6,4%%date:~3,2%%date:~0,2%.sqlite3
```

---

## Yaygın Hatalar ve Çözümleri

| Hata | Neden | Çözüm |
|---|---|---|
| `BadSignature` şifre çözme | `SECRET_KEY` değişti | Firma ayarından şifreyi tekrar gir |
| `ConnectionError` Mikro API | Sunucu IP/port yanlış | `FirmaAyar.mikro_sunucu` ve `mikro_port` kontrol et |
| `NoReverseMatch` | URL adı yanlış | `urls.py`'de `name=` parametresini kontrol et |
| `OperationalError: no such table` | Migration çalıştırılmamış | `python manage.py migrate` |

---

## Hesap Yönetimi App (`hesap_yonetimi`)

Mikro ERP'deki cari hesapları **okuma** amacıyla sorgular. Hiçbir veri yazmaz.
Tüm veriler `MikroApiClient.sql_oku()` → `SqlVeriOkuV2` endpoint'i üzerinden gelir.
Aktif firma `request.session["aktif_firma_id"]` içinde tutulur — her view `_aktif_firma(request)` ile okur.

| URL | View | Açıklama |
|---|---|---|
| `/hesap/` | `panel` | Özet panel (bakiye özeti, bağlantı durumu) |
| `/hesap/firma-sec/` | `firma_sec` | Dropdown ile aktif firma seç |
| `/hesap/firma-kartlari/` | `firma_kartlari` | Cari listesi (arama, tip filtre) |
| `/hesap/firma-kartlari/<kod>/` | `cari_detay` | Cari detay |
| `/hesap/hesap-hareketleri/` | `hesap_hareketleri` | Tarih aralığı + cari kodu ile hareketler |
| `/hesap/bakiye-raporu/` | `bakiye_raporu` | Açık bakiyeler (borç/alacak filtre) |
| `/hesap/odeme-planlama/` | `odeme_planlama` | Vadesi yaklaşan çek/senetler |

**Yeni `sql_oku()` metodu:** `sync_motor/client.py` → `MikroApiClient.sql_oku(sorgu)` → `SqlVeriOkuV2`

---

## Kod Kalitesi Araçları

### Tek Komutla Hepsini Çalıştır

```bat
kontrol.bat
```

5 aşama çalışır: ruff → vulture → pip-audit → pip outdated → django check

### Araç Listesi

| Araç | Komut | Ne Yapar | Ne Zaman |
|---|---|---|---|
| `ruff check` | `.venv\Scripts\python.exe -m ruff check .` | Linter (E/F/W/I) | VS Code'da otomatik + commit öncesi |
| `ruff format` | `.venv\Scripts\python.exe -m ruff format .` | Kod formatlama | VS Code'da otomatik |
| `vulture` | `.venv\Scripts\python.exe -m vulture sync_motor mikro_gelen hesap_yonetimi mikro_sync --min-confidence 80` | Ölü kod tespiti | Haftada 1 |
| `pip-audit` | `.venv\Scripts\python.exe -m pip_audit -r requirements.txt` | CVE güvenlik taraması | Commit öncesi |
| `pip list --outdated` | `.venv\Scripts\python.exe -m pip list --outdated` | Eski kütüphaneler | Ayda 1 |

### Vulture Yanlış Pozitif Susturma

```python
# Kullanılmayan ama Django'nun otomatik çağırdığı metotlar için:
ignore_names listesine ekle → pyproject.toml → [tool.vulture]
```

---

## Git Commit Kuralları

### Standart Akış

```bat
git status
git add -p                   ← satır satır gözden geçirerek (önerilen)
git commit -m "konu: ne yapıldı"
git push
```

### Commit Mesajı Formatı

```
<app/konu>: <ne yapıldı>
```

Örnekler:
- `hesap_yonetimi: bakiye raporu eklendi`
- `sync_motor: sql_oku() metodu eklendi`
- `güvenlik: SECRET_KEY fail-fast koruması`
- `ruff: kullanılmayan import temizlendi`

### Copilot ile Çalışma Protokolü

1. Copilot değişiklikten sonra `django check` çalıştırır — hata yoksa commit et
2. `migrate` senin sorumluluğundadır — Copilot söyler, sen çalıştırırsın
3. Her oturum sonrası: `git add . && git commit -m "..." && git push`

---

## Bağımlılık Güncelleme Kuralları

- `requirements.txt` her zaman tam sürüm (`==`) kullanır — `>=` üretimde yasak
- Yama sürüm (x.y.**Z**) → doğrudan güncelle
- Minor (x.**Y**.0) → CHANGELOG oku, test et, sonra güncelle
- Major (**X**.0.0) → ayrı branch'te test et, kasıtlı geç
- **Django**: LTS olmayan sürüme geçme — LTS→LTS atla
  - Django 5.2 LTS: Nisan 2028'e kadar destekli
- CVE bulunan paket → o gün güncelle, bekletme

---

## PDF / Excel / CSV — Türkçe Karakter Kuralları

**Bu kurallar her seferinde hatırlatılmamalıdır. Buradan oku.**

### PDF (xhtml2pdf)

```python
# DOĞRU — her ikisi de zorunlu
pisa.pisaDocument(
    BytesIO(html.encode("utf-8")),   # ← encode("utf-8") zorunlu
    buffer,
    encoding="utf-8",               # ← encoding parametresi zorunlu
)
```

HTML şablonunda:
```html
<meta charset="UTF-8">
<style>
  @font-face { font-family: DejaVu; src: url(".../DejaVuSans.ttf"); }
  body { font-family: DejaVu, sans-serif; }
</style>
```

Font: `static/fonts/DejaVuSans.ttf` (https://dejavu-fonts.github.io/)

**Hata:** `UnicodeEncodeError: 'latin-1'` → `encoding="utf-8"` eksik demektir.

### Excel (openpyxl)

openpyxl varsayılan UTF-8 kullanır. Türkçe için ekstra ayar gerekmez.  
`content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"`

### CSV

```python
response = HttpResponse(content_type="text/csv; charset=utf-8-sig")
# utf-8-sig = BOM ekler → Excel Türkçe karakterleri doğru okur
writer = csv.writer(response, delimiter=";")  # Türkiye standardı: noktalı virgül
```

**Hata:** Excel'de bozuk Türkçe → `utf-8-sig` yerine `utf-8` kullanılmış demektir.

