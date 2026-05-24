# Mikro Jump Bridge

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://python.org)
[![Django](https://img.shields.io/badge/Django-5.2_LTS-green)](https://djangoproject.com)

**Mikro ERP'yi doğrudan sorgulayan çok firmalı cari hesap ve hareket yönetim köprüsü.**
Django + SQLite tabanlı, kurulum gerektirmez — `baslat.bat` tek tıkla başlatmak için yeterlidir.

---

## Mimari

```
Mikro ERP API  (port 8094)
      ↕  MikroApiClient  (MD5 günlük hash auth)
hesap_yonetimi/  (cari/hareket/bakiye sorgulama — sadece okuma)
sync_motor/      (firma ayarları, bağlantı testi, import geçmişi)
```

> Uygulama Mikro ERP'ye **yazma yapmaz**; cari hesap, hareket ve bakiye verilerini okuyup yerel veritabanında **ayar/oturum** bilgisini saklar.

---

## Özellikler

| Özellik | Açıklama |
|---|---|
| **Çoklu Firma** | Birden fazla Mikro ERP firmasını tek arayüzden yönet |
| **Bağlantı Testi** | LAN / VPN / Uzak Masaüstü IP'leri ile sağlık kontrolü |
| **Cari Hesap Sorgulama** | Mikro ERP'deki cariler, hareketler ve açık bakiyeler okunur |
| **Ödeme Planlama** | Vadesi yaklaşan çek/senet takibi |
| **Şifreli Bağlantı** | Mikro şifreleri `django.core.signing` ile şifreli saklanır |
| **Kullanıcı Yönetimi** | Kullanıcı ekleme, silme, şifre değiştirme, yetkilendirme |
| **Posta / Ekstre** | SMTP ayarları ve cari ekstre e-postalama |
| **Lisans Sistemi** | 15 gün ücretsiz deneme; HMAC imzalı lisans anahtarıyla aktivasyon |
| **PDF / Excel / CSV** | Türkçe karakter destekli rapor çıktıları |

---

## Hızlı Başlangıç

### Gereksinim
- Python 3.10 veya üzeri (https://python.org)

> **Detaylı adım adım kurulum:** [KURULUM.md](KURULUM.md)

### Başlatma

```bat
baslat.bat
```

İlk çalışmada otomatik olarak:
1. Sanal Python ortamı oluşturur (`.venv/`)
2. Gerekli paketleri kurar
3. Veritabanını hazırlar (`db.sqlite3`)
4. Admin kullanıcı oluşturur (`.env`'deki `ADMIN_KULLANICI`/`ADMIN_SIFRE` ile sessizce; tanımlı değilse interaktif sorar)

Ardından tarayıcınızda:

- **Uygulama:** http://127.0.0.1:8001
- **Admin paneli:** http://127.0.0.1:8001/admin

---

## Teknoloji Yığını

- **Django 5.2 LTS** + SQLite 3
- **Bootstrap 5.3** + Bootstrap Icons (CDN)
- **requests 2.34** — Mikro ERP API HTTP istemcisi
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
├── olustur_admin.py        ← Admin kullanıcı oluşturma (sessiz/interaktif)
├── manage.py
├── db.sqlite3              ← Tüm veri (yedek = bu dosyayı kopyala)
├── pyproject.toml          ← Ruff + Vulture konfigürasyonu
├── requirements.txt        ← Üretim bağımlılıkları (tam sürüm ==)
├── requirements-dev.txt    ← Geliştirme araçları (ruff, vulture, pip-audit)
├── .env                    ← Ortam değişkenleri (Git'e gönderilmez)
├── logs/
│   └── mikro_sync.log      ← INFO+ kayıtlar (10 MB × 3 yedek)
├── docs/
│   ├── runbooks/           ← Geliştirme standartları ve kararlar (01-18)
│   └── arsiv/              ← Pasif/arşivlenmiş notlar
├── templates/
│   ├── base.html           ← Ana layout
│   ├── registration/
│   ├── sync_motor/         ← Firma, import geçmişi şablonları
│   ├── hesap_yonetimi/     ← Cari sorgulama şablonları
│   ├── kullanici/          ← Kullanıcı yönetimi şablonları
│   ├── lisans/             ← Lisans şablonları
│   └── posta/              ← Posta ayar/ekstre şablonları
├── mikro_sync/             ← Django proje paketi
│   ├── settings.py
│   ├── urls.py
│   ├── middleware.py       ← LoginZorunluMiddleware, FirmaSecimZorunluMiddleware
│   └── forms_mixin.py      ← BootstrapFormMixin
├── sync_motor/             ← Firma ayarları + bağlantı testi + import geçmişi
│   ├── models.py           ← FirmaAyar, ImportLog
│   ├── client.py           ← MikroApiClient (MD5 auth, sql_oku)
│   ├── views.py
│   └── urls.py
├── hesap_yonetimi/         ← Cari hesap sorgulama (sadece okuma)
│   ├── views.py            ← panel, firma_kartlari, hesap_hareketleri, bakiye_raporu
│   └── urls.py
├── kullanici/              ← Kullanıcı yönetimi (liste, ekle, sil, şifre, yetki)
├── lisans/                 ← Deneme + lisans aktivasyon (middleware ile kontrol)
├── posta/                  ← SMTP ayarları + cari ekstre e-postalama
└── installer/              ← Inno Setup paketleme (setup.iss, baslat_kurulu.bat)
```

---

## Ortam Değişkenleri (.env)

Proje kökünde `.env` dosyası oluşturun (`.gitignore`'da, asla Git'e gönderilmez):

```ini
SECRET_KEY=guclu-uretilmis-anahtar
DEBUG=False
ALLOWED_HOSTS=127.0.0.1,localhost

ADMIN_KULLANICI=admin
ADMIN_SIFRE=GucluBirSifre123!
```

> `SECRET_KEY` değeri `django-insecure-` ile başlıyorsa ve `DEBUG=False` ise uygulama başlamaz.

`.env` tek otorite şifre kaynağıdır ve `.gitignore`'dadır. Mikro ERP firma şifreleri DB'de `django.core.signing.Signer` ile imzalanmış şekilde saklanır — ayrı bir düz metin kasa tutulmaz.

---

## Veri Yedekleme

Tüm veri `db.sqlite3` dosyasındadır. Yedeklemek için bu dosyayı kopyalayın:

```bat
copy db.sqlite3 db_yedek_%date:~6,4%%date:~3,2%%date:~0,2%.sqlite3
```

Yerel yedek dizini `yedek/` klasörü `.gitignore`'dadır.

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

Tam kod örnekleri: [docs/runbooks/18-pdf-excel-turkce-karakter.md](docs/runbooks/18-pdf-excel-turkce-karakter.md)

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
