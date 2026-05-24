# Mikro Jump Bridge

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://python.org)
[![Django](https://img.shields.io/badge/Django-5.2_LTS-green)](https://djangoproject.com)

**Mikro ERP'yi doğrudan sorgulayan, çok firmalı cari hesap yönetimi ve iki yönlü senkronizasyon köprüsü.**
Django + SQLite tabanlı, kurulum gerektirmez — `baslat.bat` tek tıkla çalıştırmak için yeterlidir.

---

## Bağlantı Mimarisi

```
Mikro ERP API  (port 8094)
      ↕  MikroApiClient  (MD5 günlük hash auth)
mikro_gelen/   (staging — ham veriler)
      ↕
hesap_yonetimi/  (cari sorgulama — okuma amaçlı)
```

---

## Özellikler

| Özellik | Açıklama |
|---|---|
| **Firma Yönetimi** | Birden fazla Mikro ERP firmasını tek arayüzden yönet |
| **Otomatik Eşleştirme** | VKN + SequenceMatcher tabanlı öğrenen cari eşleştirme |
| **5 Adımlı Pipeline** | Çekme → Eşleştirme → Onay → Aktarım → Doğrulama |
| **Staging Alanı** | Ham Mikro faturaları `mikro_gelen/` üzerinde karantinaya alınır |
| **Onay Ekranı** | Otomatik eşleştirilemeyen cariler kullanıcı onayına sunulur |
| **Import Geçmişi** | Her aktarım için tam log; başarı yüzdesi, hata detayı |
| **Cari Hesap Sorgulama** | Mikro ERP'deki cariler, hareketler ve bakiyeler okunur |
| **Şifreli Bağlantı** | Mikro şifreleri `django.core.signing` ile şifreli saklanır |
| **Lisans Sistemi** | 15 gün ücretsiz deneme; HMAC imzalı lisans anahtarıyla aktivasyon |

---

## Hızlı Başlangıç

### Gereksinim
- Python 3.10 veya üzeri (https://python.org)

> **Detaylı adım adım kurulum:** [KURULUM.md](KURULUM.md)

### Başlatma (ilk kez veya sonradan)

```bat
baslat.bat
```

İlk çalışmada otomatik olarak:
1. Sanal Python ortamı oluşturur (`.venv/`)
2. Gerekli paketleri kurar
3. Veritabanını hazırlar (`db.sqlite3`)
4. Admin kullanıcı oluşturur (interaktif)

Ardından tarayıcınızda:

- **Uygulama:** http://127.0.0.1:8001
- **Admin paneli:** http://127.0.0.1:8001/admin

---

## Teknoloji Yığını

- **Django 5.2 LTS** + SQLite 3
- **Bootstrap 5.3** + Bootstrap Icons (CDN)
- **requests 2.32** — Mikro ERP API HTTP istemcisi
- **defusedxml 0.7** — Güvenli XML parse
- **whitenoise** — Statik dosya sunumu
- **django-widget-tweaks** — Şablon form widget'ları
- **python-decouple** — `.env` tabanlı ayar yönetimi
- **ruff** — Linter ve kod formatlayıcı

---

## Proje Yapısı

```
C:\mikro_jump_bridge\
├── baslat.bat              ← Tek tıkla başlat
├── kontrol.bat             ← Kod kalitesi: ruff+vulture+pip-audit+django check
├── olustur_admin.py        ← Admin kullanıcı oluşturma (interaktif)
├── manage.py
├── db.sqlite3              ← Tüm veri (yedek = bu dosyayı kopyala)
├── pyproject.toml          ← Ruff + Vulture konfigürasyonu
├── requirements.txt        ← Üretim bağımlılıkları (tam sürüm ==)
├── requirements-dev.txt    ← Geliştirme araçları (ruff, vulture, pip-audit)
├── .env                    ← Ortam değişkenleri (Git'e gönderilmez)
├── logs/
│   └── mikro_sync.log      ← INFO+ kayıtlar (10 MB × 3 yedek)
├── docs/
│   └── runbooks/           ← Geliştirme standartları ve kararlar (01-18)
├── templates/
│   ├── base.html           ← Ana layout
│   ├── registration/
│   ├── sync_motor/         ← Firma, import, onay şablonları
│   ├── mikro_gelen/        ← Staging fatura listeleri
│   └── hesap_yonetimi/     ← Cari sorgulama şablonları
├── mikro_sync/             ← Django proje paketi
│   ├── settings.py
│   ├── urls.py
│   ├── middleware.py       ← LoginZorunluMiddleware
│   └── forms_mixin.py      ← BootstrapFormMixin
├── sync_motor/             ← Ana uygulama
│   ├── models.py           ← FirmaAyar, ImportLog
│   ├── client.py           ← MikroApiClient (MD5 auth, sql_oku)
│   ├── views.py
│   └── urls.py
├── mikro_gelen/            ← Staging alanı
│   ├── models.py           ← MikroFatura, MikroCariHesap, MikroStokKarti
│   ├── views.py
│   └── urls.py
└── hesap_yonetimi/         ← Cari hesap sorgulama (sadece okuma)
    ├── views.py            ← panel, firma_kartlari, hesap_hareketleri, bakiye_raporu
    └── urls.py
```

---

## Ortam Değişkenleri (.env)

Proje kökünde `.env` dosyası oluşturun (`.gitignore`'da, asla Git'e gönderilmez):

```ini
SECRET_KEY=guclu-uretilmis-anahtar
DEBUG=False
ALLOWED_HOSTS=127.0.0.1,localhost
```

> `SECRET_KEY` değeri `django-insecure-` ile başlıyorsa ve `DEBUG=False` ise uygulama başlamaz.

---

## Veri Yedekleme

Tüm veri `db.sqlite3` dosyasındadır. Yedeklemek için bu dosyayı kopyalayın:

```bat
copy db.sqlite3 db_yedek_%date:~6,4%%date:~3,2%%date:~0,2%.sqlite3
```

---

## Geliştirici Notları

### Kod Kalitesi — Tek Komut

```bat
kontrol.bat
```

5 aşama çalışır: **ruff** (linter) → **vulture** (ölü kod) → **pip-audit** (CVE) → **pip outdated** (güncellik) → **django check**

### Migration oluştur ve uygula

```bat
.venv\Scripts\python manage.py makemigrations
.venv\Scripts\python manage.py migrate
```

### Git Akışı

```bat
git status
git add -p                        ← satır satır gözden geçirerek
git commit -m "app: ne yapıldı"   ← örnek: "hesap_yonetimi: bakiye raporu eklendi"
git push
```

### PDF / Excel Türkçe Karakter Özeti

- **PDF (xhtml2pdf):** `BytesIO(html.encode("utf-8"))` + `encoding="utf-8"` + DejaVu font — her üçü zorunlu
- **Excel (openpyxl):** Ekstra ayar gerekmez, UTF-8 varsayılan
- **CSV:** `utf-8-sig` encoding (BOM ile) + `;` ayraç — Excel için zorunlu

Tam kod örnekleri: `docs/runbooks/18-pdf-excel-turkce-karakter.md`

---

## Yaygın Hatalar

| Hata | Neden | Çözüm |
|---|---|---|
| `BadSignature` şifre çözme | `SECRET_KEY` değişti | Firma ayarından şifreyi tekrar gir |
| `ConnectionError` Mikro API | Sunucu IP/port yanlış | `FirmaAyar.mikro_sunucu` ve `mikro_port` kontrol et |
| `OperationalError: no such table` | Migration çalıştırılmamış | `python manage.py migrate` çalıştır |

---

## Katkıda Bulunma

Lütfen önce [CONTRIBUTING.md](CONTRIBUTING.md) dosyasını okuyun.
Geliştirme standartları için `docs/runbooks/` klasörüne bakın.

---

## Lisans

Bu proje [MIT Lisansı](LICENSE) ile lisanslanmıştır.
