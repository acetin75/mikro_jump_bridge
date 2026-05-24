# Runbook 02 — Kimlik doğrulama, yetkilendirme ve API güvenliği

**Faz:** P0  
**Durum:** ❌ Geçersiz (2026-05-24) — MB entegrasyonu kaldırıldı; bu runbook yalnızca Mikro ERP API auth kapsamında güncellenmeli

### Yapılan değişiklikler

| Dosya | Değişiklik |
|---|---|
| `sync_motor/client.py` | MB entegrasyonu tamamen kaldırıldı (2026-05-23) |
| `sync_motor/models.py` | MB entegrasyon alanları (`mb_api_url`, `mb_api_token`, `yon`) silindi |

**Açık kalan:** Rotate edilebilir token altyapısı, URL-regex yerine view-düzeyinde yetki (P1).

## Amaç

Kullanıcı ve entegrasyon erişimlerinin tahmine, URL kalıbına veya düz metin token'a bırakılmadığı bir güvenlik standardı kurmak.

## Mevcut durum ve kanıtlar

### 1) Mikro ERP API yalnızca MD5 hash doğrulamasıyla korunuyor

**Kanıtlar:**

- `sync_motor/client.py` → her istekte `MD5("YYYY-MM-DD " + sifre)` hash gönderilir
- Token yaşam döngüsü yok, rotation yok

**Risk:**

- Mikro ERP şifresi ele geçirilirse tüm API erişimi açılır.

### 2) Yetkilendirme URL isimlendirme kalıplarına bağımlı

**Kanıtlar:**

- `mikro_sync/middleware.py` → `LoginZorunluMiddleware` + `FirmaSecimZorunluMiddleware`
- View seviyesinde açık izin sözleşmesi yok.

**Risk:**

- URL adı değişirse yetki de fiilen değişebilir.

### 3) API kimlik doğrulaması için standart Django token altyapısı etkin değil

**Kanıtlar:**

- `requirements.txt` içinde DRF yok.
- `INSTALLED_APPS` içinde `rest_framework` veya `rest_framework.authtoken` altyapısı yok.

**Risk:**

- Dış entegrasyon gerektiğinde token altyapısı sıfırdan eklenmek zorunda.

## Hedef standart

- API erişimi sürülebilir, döndürülebilir ve izlenebilir kimlik bilgileriyle korunmalı.
- Yetkiler URL regex'i yerine view veya servis seviyesinde açık tanımlanmalı.
- API ve UI güvenlik modelleri birbirinden net ayrılmalı.

## Önerilen uygulama yaklaşımı

1. Mikro Sync entegrasyonu için standart bir API auth modeli seç:
   - DRF token
   - imzalı servis hesabı
   - zaman sınırlı bearer token
2. `csrf_exempt` kullanımını entegrasyon tasarımına göre yeniden değerlendir.
3. Tüm yazma/silme view'larında decorator veya ortak permission wrapper kullan.
4. Yetki denetimini URL regex yerine işlem niyetine bağla.
5. Admin paneline erişim için grup/politika kontrolü ekle.

## Kabul kriterleri

- Yetki, URL kalıbına değil açık bir policy katmanına bağlı olur.
- Entegrasyon token'ları rotate edilebilir hale gelir.
- API istekleri için kimlik doğrulama ve yetki senaryolarını doğrulayan testler yazılır.
- Muhasebeci / Yönetici / Görüntüleyici davranışı net olarak testle güvenceye alınır.

## Sonraki iş paketleri

- P0.4 — API auth modelini tasarla
- P1.1 — View bazlı yetki denetimi çıkar
- P1.2 — Rol matrisi ve yetki testleri ekle
