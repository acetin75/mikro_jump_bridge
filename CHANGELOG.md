# Sürüm Notları

Bu projenin sürüm notları [Keep a Changelog](https://keepachangelog.com/tr/1.1.0/) formatını izler ve [Semantik Sürümleme](https://semver.org/lang/tr/) kurallarına uyar.

## [Yayınlanmadı]

### Eklendi
- `sync_motor/sql_utils.py` — Decimal-güvenli SQL yardımcıları (sql_str, sql_like, sql_int, sql_date, whitelist)
- `MikroApiClient._extract_list_response()` — API list yanıt normalleştirme
- `static/css/app.css`, `static/css/firma_sec.css`, `static/js/app.js`, `static/js/firma_sec.js` — Inline CSS/JS harici dosyalara taşındı
- 41 yeni test: `sync_motor/test_client.py` (MikroApiClient + sql_utils mock), `lisans/tests.py` (HMAC imza + singleton), `posta/tests.py` (singleton + form), `hesap_yonetimi/tests.py` (_guvenli_next + open-redirect)
- `.github/workflows/ci.yml` — requirements-dev + ruff format check + pip-audit
- `kontrol.bat` — 6 aşamalı fail-fast (ruff lint/format, vulture, pip-audit, check, test)

### Değiştirildi
- `baslat.bat` — admin oluşturma başarısızlığında fail-fast (UYARI → HATA + exit 1)
- `installer/setup.iss` + `release.yml` — `.env.example` tek kaynak (gereksiz kopyalama kaldırıldı)
- `templates/base.html` — Mesajlar artık tek yerde (topbar badge tekrarı kaldırıldı)
- `mikro_sync/settings.py` — `STATICFILES_DIRS` eklendi
- README — PDF/Excel/CSV özelliği "planlanan" olarak işaretlendi
- 48 dosya `ruff format` ile normalize edildi

### Güvenlik
- `SECRET_KEY` fail-fast genişletildi: placeholder kalıpları (`buraya`, `change`, `example`) + minimum uzunluk + entropi kontrolü
- `olustur_admin.py` — Zayıf/placeholder admin şifreleri reddedilir
- `hesap_yonetimi.firma_sec` — Açık yönlendirme koruması (`_guvenli_next`)
- `MailAyar` — SMTP TLS doğrulama opsiyonel (`tls_dogrulamayi_atla` alanı)

### Kaldırıldı
- `defusedxml==0.7.1` — Kullanılmıyordu, `requirements.txt`'den çıkarıldı

## [1.0.0] - 2026-05-24

İlk kararlı sürüm. Mikro ERP'ye **sadece okuma** modunda bağlanan çok firmalı cari yönetim köprüsü.

### Eklendi
- `sync_motor` — Firma ayarları, bağlantı testi, `MikroApiClient` (MD5 günlük hash auth, port 8094)
- `sync_motor.client.sql_oku()` — `SqlVeriOkuV2` üzerinden serbest SQL sorgusu
- `hesap_yonetimi` — Panel, cari kartları, hesap hareketleri, bakiye raporu, ödeme planlama (sadece okuma)
- `kullanici` — Liste, ekle, sil, şifre değiştir, yetkilendirme
- `lisans` — 15 gün ücretsiz deneme + HMAC-SHA256 imzalı lisans anahtarı doğrulama + middleware kontrolü
- `posta` — SMTP ayarları + cari ekstre e-postalama
- `baslat.bat` — Sanal ortam, paket kurulumu, migrate, admin oluşturma otomatik
- `kontrol.bat` — 5 aşamalı kod kalitesi: ruff + vulture + pip-audit + pip outdated + django check
- `olustur_admin.py` — `.env`'den sessiz veya interaktif admin oluşturma
- `installer/setup.iss` — Inno Setup ile Windows kurulum paketi
- `docs/runbooks/` — 18 konuda geliştirme standardı
- `LoginZorunluMiddleware`, `LisansKontrolMiddleware`, `FirmaSecimZorunluMiddleware`
- PDF/Excel/CSV Türkçe karakter desteği (DejaVu fontu, utf-8-sig)

### Güvenlik
- `SECRET_KEY` fail-fast koruması (`django-insecure-` + `DEBUG=False` ile uygulama başlamaz)
- Mikro şifreleri `django.core.signing.Signer` ile imzalanmış olarak saklanır
- Mikro API'ye günlük MD5 hash auth (şifre açık metin gönderilmez)
- `.env` `.gitignore`'da
- `yedek/` dizini `.gitignore`'da (yedek dosyaları Git'e gönderilmez)

### Teknoloji
- Django 5.2 LTS (Nisan 2028'e kadar destekli)
- Python 3.10+
- SQLite 3
- Bootstrap 5.3 + Bootstrap Icons
- requests 2.34, defusedxml 0.7, whitenoise, django-widget-tweaks, python-decouple
- ruff (linter + format), vulture (ölü kod), pip-audit (CVE)

### Kaldırıldı
- `mikro_gelen` uygulaması — staging tablosu, `MikroFatura` modeli, `import_baslat()` view'ı (yazma akışı projeden çıkarıldı; köprü sadece okuma modunda)
- README/copilot-instructions/runbook'lardan "iki yönlü senkronizasyon", "staging onay ekranı", "5 adımlı pipeline", "otomatik eşleştirme" gibi yanlış reklam metinleri

[1.0.0]: https://github.com/acetin75/mikro_jump_bridge/releases/tag/v1.0.0
