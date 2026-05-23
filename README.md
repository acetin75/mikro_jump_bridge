# Muhasebe Bürosu CRM

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://python.org)
[![Django](https://img.shields.io/badge/Django-5.2-green)](https://djangoproject.com)
[![GitHub release](https://img.shields.io/github/v/release/acetin75/muhasebe-buro-crm)](https://github.com/acetin75/muhasebe-buro-crm/releases)

Küçük ve orta ölçekli muhasebe büroları için geliştirilmiş, **yerel** çalışan web tabanlı büro yönetim sistemi.
Kurulum gerektirmez — `baslat.bat` tek tıkla çalıştırmak için yeterlidir.

---

## Ekran Görüntüleri

| Dashboard | Fatura | Çek & Senet |
|---|---|---|
| ![Dashboard](docs/screenshots/dashboard.png) | ![Fatura](docs/screenshots/fatura.png) | ![Ceksenet](docs/screenshots/ceksenet.png) |

> **Not:** Ekran görüntüleri için uygulamayı başlatın, ilgili sayfaların ekran görüntüsünü alıp `docs/screenshots/` klasörüne kaydedin.

---

## Özellikler

| Modül | Açıklama |
|---|---|
| **Cari Hesaplar** | Müşteri/tedarikçi kayıtları, borç/alacak hareketleri |
| **Banka** | Banka hesapları, ekstre yükleme (PDF/Excel parse), hareket eşleştirme |
| **Sözleşmeler** | Sözleşme takibi, bitiş tarihi uyarıları |
| **Tahsilat** | Tahsilat/ödeme kayıtları |
| **Fatura + KDV** | Satış/alış fatura, kalem bazlı KDV özeti, PDF baskı |
| **Çek & Senet** | Çek/senet vade takibi, durum yönetimi |
| **Gider** | Gider kategorileri, KDV dahil gider takibi |
| **Raporlar** | 4 Excel raporu (cari bakiye, ekstre, tahsilat, gider) + dönemsel özet |
| **Dashboard** | Bildirim paneli — vadesi geçenler, yaklaşan tarihler |
| **Vergi Takvimi** | Türkiye vergi/beyanname takvimi, renk kodlu hatırlatmalar |
| **E-Fatura XML** | GİB UBL-TR 2.1 uyumlu e-fatura XML üretimi (satış faturaları) |
| **Çoklu Kullanıcı** | Yönetici / Muhasebeci / Görüntüleyici rol sistemi, aktivite logu |

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
4. Admin kullanıcı oluşturur (`admin` / `admin123`)
5. Tarayıcıyı otomatik açar

Ardından tarayıcınızda:

- **Uygulama:** http://127.0.0.1:8000
- **Admin paneli:** http://127.0.0.1:8000/admin
- **Kullanıcı / Şifre:** `admin` / `admin123`

---

## Teknoloji Yığını

- **Django 5.2** + SQLite 3
- **Bootstrap 5.3** + Bootstrap Icons (CDN)
- **xhtml2pdf** — PDF baskı
- **openpyxl** — Excel export/import
- **pdfplumber** — Banka ekstresi PDF parse
- **whitenoise** — Statik dosya sunumu
- **django-widget-tweaks** — Şablon form widget'ları
- **django-debug-toolbar** — Geliştirici SQL profiler (`DEBUG=True`)
- **ruff** — Linter ve kod formatlayıcı

---

## Proje Yapısı

```
muhasebe_buro/
├── baslat.bat              ← Başlatma scripti
├── olustur_admin.py        ← Admin hesabı oluşturma
├── manage.py
├── db.sqlite3              ← Tüm veri (yedek = bu dosyayı kopyala)
├── pyproject.toml          ← Ruff konfigürasyonu
├── requirements.txt
├── logs/
│   ├── hata.log            ← HATA kayıtları (5 MB × 5)
│   └── uygulama.log        ← Bilgi kayıtları (10 MB × 3)
├── templates/              ← Tüm HTML şablonlar (global)
│   └── base.html           ← Ana layout
├── static/
├── muhasebe_buro/
│   ├── settings.py
│   ├── middleware.py       ← LoginZorunluMiddleware
│   └── forms_mixin.py      ← BootstrapFormMixin
├── cari/
├── banka/
├── sozlesme/
├── tahsilat/
├── fatura/
├── ceksenet/
├── gider/
├── rapor/
└── dashboard/
```

---

## Veri Yedekleme

Tüm veri `db.sqlite3` dosyasındadır. Yedeklemek için bu dosyayı kopyalayın:

```bat
copy db.sqlite3 db_yedek_%date:~6,4%%date:~3,2%%date:~0,2%.sqlite3
```

---

## Geliştirici Notları

### Migration oluştur ve uygula

```bat
.venv\Scripts\python manage.py makemigrations
.venv\Scripts\python manage.py migrate
```

### Linter çalıştır (ruff)

```bat
.venv\Scripts\ruff check .
.venv\Scripts\ruff format .
```

### E-posta hatırlatma komutu

```bat
:: Vadeleri 7 gün içinde dolacak çek/senetleri bildir
.venv\Scripts\python manage.py hatirlatma_gonder --gun 7

:: Vadesi geçmiş tüm çek/senetleri bildir
.venv\Scripts\python manage.py hatirlatma_gonder --vadesi_gecenler
```

---

## Önemli Alan İsimleri (Yaygın Karışıklıklar)

| Model | Doğru | Yanlış |
|---|---|---|
| `cari.Cari` | `.ad` | ~~`.unvan`~~ ~~`.name`~~ |
| `cari.HesapHareketi` | `.borc` / `.alacak` | ~~`.tutar`~~ |
| URL (cari) | `cari_detay` | ~~`cari:detay`~~ |
| URL (fatura) | `fatura_listesi` | ~~`fatura:list`~~ |
| URL (çek/senet) | `{% url 'ceksenet:list' %}` | ~~`ceksenet_list`~~ |

---

## URL Namespace Referansı

| App | Namespace | Örnek |
|---|---|---|
| cari | — (flat) | `cari_listesi`, `cari_detay` |
| banka | — (flat) | `banka_hesap_listesi` |
| sozlesme | — (flat) | `sozlesme_listesi` |
| tahsilat | — (flat) | `tahsilat_listesi` |
| fatura | — (flat) | `fatura_listesi`, `kdv_ozet` |
| ceksenet | `ceksenet:` | `ceksenet:list`, `ceksenet:ekle` |
| gider | `gider:` | `gider:list`, `gider:ekle` |
| rapor | `rapor:` | `rapor:index`, `rapor:donemsel` |

---

## Loglama

```python
import logging
logger = logging.getLogger("muhasebe")

logger.info("Fatura oluşturuldu: %s", fatura_no)
logger.error("Hata", exc_info=True)
```

Log dosyaları: `logs/hata.log` ve `logs/uygulama.log`

---

## Ortam Değişkenleri (.env)

Üretim ortamı veya e-posta özelliği için `.env.example` dosyasını kopyalayın:

```bat
copy .env.example .env
```

`.env` dosyasını düzenleyerek `SECRET_KEY`, `DEBUG` ve e-posta bilgilerini ayarlayın.
Bu dosya `.gitignore`'a eklidir — asla Git'e gönderilmez.

---

## Katkıda Bulunma

Katkılarınızı memnuniyetle karşılıyoruz! Lütfen önce [CONTRIBUTING.md](CONTRIBUTING.md)
dosyasını okuyun.

Hata bildirmek için GitHub Issues, özellik önermek için GitHub Discussions kullanın.

---

## Lisans

Bu proje [MIT Lisansı](LICENSE) ile lisanslanmıştır.
