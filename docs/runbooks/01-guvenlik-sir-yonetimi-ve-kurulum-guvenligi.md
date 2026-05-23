# Runbook 01 — Güvenlik, sır yönetimi ve ilk kurulum güvenliği

**Faz:** P0  
**Durum:** ✅ Tamamlandı (2026-05-23)

### Yapılan değişiklikler

| Dosya | Değişiklik |
|---|---|
| `olustur_admin.py` | Sabit `admin123` kaldırıldı; `secrets.token_urlsafe(16)` ile rastgele parola üretilir, konsola bir kez basılır |
| `muhasebe_buro/settings.py` | `AUTH_PASSWORD_VALIDATORS` — Django'nun 4 varsayılan doğrulaycısı açıldı, min uzunluk 10 |
| `muhasebe_buro/settings.py` | `SECRET_KEY` fail-fast: `DEBUG=False` + placeholder kombinasyonunda `RuntimeError` |
| `muhasebe_buro/settings.py` | `MIKRO_SYNC_API_TOKEN` fail-fast: aynı kural |
| `muhasebe_buro/settings.py` | `DEBUG=False` koşulunda üretim güvenlik ayarları otomatik aktif: `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_CONTENT_TYPE_NOSNIFF`, `X_FRAME_OPTIONS`, `CSRF_TRUSTED_ORIGINS` |

## Amaç

Projede üretime çıkışı doğrudan riske atan güvenlik açıklarını kapatmak:

- varsayılan parolalar
- zayıf parola politikası
- üretim sertleştirme eksikleri
- sır yönetiminde gevşeklik

## Neden kritik

Bu başlık kapatılmadan yapılacak her yeni geliştirme, temeli gevşek bir binaya yeni kat çıkmak gibi olur.

## Mevcut durum ve kanıtlar

### 1) Varsayılan admin hesabı ve parola hard-coded

**Kanıtlar:**

- `olustur_admin.py` → `User.objects.create_superuser("admin", "admin@localhost", "admin123")`
- `baslat.bat` → `Kullanici: admin  /  Sifre: admin123`
- `README.md` → ilk giriş için `admin / admin123`
- `KURULUM.md` → ilk giriş için `admin / admin123`

**Risk:**

- Kurulum yapan herkes aynı bilinen parolayla başlıyor.
- Parola değiştirilmezse sistem fiilen tahmin edilebilir kimlik bilgileriyle açılmış oluyor.

### 2) Parola doğrulayıcıları kapalı

**Kanıt:**

- `muhasebe_buro/settings.py` → `AUTH_PASSWORD_VALIDATORS = []`

**Risk:**

- kısa, yaygın veya tamamen zayıf parolalar kabul edilir.
- kullanıcı güvenliği proje disiplinine bırakılmış olur.

### 3) Güvenli üretim ayarları tanımlı değil

**Kanıt:**

- `muhasebe_buro/settings.py` içinde şu ayarlar yok:
  - `SECURE_SSL_REDIRECT`
  - `SESSION_COOKIE_SECURE`
  - `CSRF_COOKIE_SECURE`
  - `SECURE_HSTS_SECONDS`
  - `SECURE_PROXY_SSL_HEADER`
  - `CSRF_TRUSTED_ORIGINS`

**Risk:**

- Yerel kullanım hedeflense bile kurumsal ortama taşınırsa sertleştirme checklist'i eksik kalır.
- Güvenli dağıtım politikası kod seviyesinde tanımlanmamış olur.

### 4) Varsayılanlar güvenli değil

**Kanıtlar:**

- `muhasebe_buro/settings.py` → `DEBUG` varsayılanı `True`
- `muhasebe_buro/settings.py` → `SECRET_KEY` varsayılanı tahmin edilebilir bir placeholder
- `muhasebe_buro/settings.py` → `MIKRO_SYNC_API_TOKEN` varsayılanı üretim için uygun değil

**Risk:**

- Ortam değişkeni yüklenmezse sistem güvensiz varsayılanlarla açılabilir.

## Hedef standart

- Varsayılan admin parolası kaldırılmalı.
- İlk kurulumda rastgele parola üretilmeli veya zorunlu kullanıcı girişi alınmalı.
- Django varsayılan parola doğrulayıcıları etkinleştirilmeli.
- Üretim sertleştirme ayarları `.env` üzerinden yönetilmeli.
- Güvenli varsayılan yaklaşımı benimsenmeli: kritik sır yoksa servis fail-fast davranmalı.

## Önerilen uygulama yaklaşımı

1. `olustur_admin.py` içinde sabit parola kullanımını kaldır.
2. `baslat.bat` içinde ya rastgele parola üret ya da ilk kurulum akışında kullanıcıya parola belirlet.
3. `AUTH_PASSWORD_VALIDATORS` için Django'nun varsayılan 4 doğrulayıcısını aç.
4. `DEBUG=False` senaryosunda güvenlik ayarlarını zorunlu hale getir.
5. `SECRET_KEY` ve `MIKRO_SYNC_API_TOKEN` için üretimde placeholder kabul etmeyen kontrol ekle.

## Kabul kriterleri

- Sabit `admin123` hiçbir dosyada geçmez.
- `python manage.py check --deploy` temiz döner.
- Üretimde `DEBUG=True` ile açılış engellenir veya yüksek görünürlüklü hata verir.
- Zayıf parola denemeleri reddedilir.

## Sonraki iş paketleri

- P0.1 — Kurulum güvenliğini refactor et
- P0.2 — Güvenlik ayarlarını `.env` tabanlı hale getir
- P0.3 — Güvenlik doğrulama checklist'i ekle
