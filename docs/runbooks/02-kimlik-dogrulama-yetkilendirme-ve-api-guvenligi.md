# Runbook 02 — Kimlik doğrulama, yetkilendirme ve API güvenliği

**Faz:** P0  
**Durum:** 🟡 Kısmi (2026-05-23) — token bug düzeldi; kapsamlı auth P1'de

### Yapılan değişiklikler

| Dosya | Değişiklik |
|---|---|
| `muhasebe_buro/api_views.py` | `auth_token__key` — `rest_framework.authtoken` yüklenmediği halde `User.objects.filter(auth_token__key=...)` yapan sessiz-başarısız sorgu kaldırıldı; doğrulama yalnızca `_token_basit_dogrula` üzerinden yürüyüyor |
| `muhasebe_buro/api_views.py` | Kullanılmayan `User` import temizlendi |

**Açık kalan:** Rotate edilebilir token altyapısı, URL-regex yerine view-düzeyinde yetki (P1).

## Amaç

Kullanıcı ve entegrasyon erişimlerinin tahmine, URL kalıbına veya düz metin token'a bırakılmadığı bir güvenlik standardı kurmak.

## Mevcut durum ve kanıtlar

### 1) API doğrulaması düz metin token karşılaştırmasına dayanıyor

**Kanıtlar:**

- `muhasebe_buro/api_views.py` → `_token_basit_dogrula(token)`
- `muhasebe_buro/api_views.py` → `settings.MIKRO_SYNC_API_TOKEN` ile string karşılaştırması

**Risk:**

- token yaşam döngüsü yok
- rotation yok
- scope yok
- erişim kaydında güçlü kimlik temsili yok

### 2) Yazma endpoint'i `csrf_exempt`

**Kanıt:**

- `muhasebe_buro/api_views.py` → `@csrf_exempt` ile `fatura_aktar`

**Risk:**

- API web bağlamında yanlış konumlandırılırsa saldırı yüzeyi büyür.
- Güvenlik politikası framework tarafından değil, yorumlarla korunuyor.

### 3) Yetkilendirme URL isimlendirme kalıplarına bağımlı

**Kanıtlar:**

- `muhasebe_buro/permissions.py` → `_SIL_RE = re.compile(r"/sil/")`
- `muhasebe_buro/permissions.py` → `_YAZMA_RE = re.compile(r"/(ekle|duzenle|yukle|eslestir|durum)/")`
- Aynı dosyada decorator yapısı olmasına rağmen grep sonucunda decorator kullanımı esasen `kullanici/views.py` ile sınırlı.

**Risk:**

- URL adı değişirse yetki de fiilen değişebilir.
- View seviyesinde açık bir izin sözleşmesi yok.
- Güvenlik davranışı isimlendirme konvansiyonuna bağımlı kalıyor.

### 4) API kimlik doğrulaması için standart Django token altyapısı etkin değil

**Kanıtlar:**

- `requirements.txt` içinde DRF yok.
- `INSTALLED_APPS` içinde `rest_framework` veya `rest_framework.authtoken` altyapısı yok.
- `muhasebe_buro/api_views.py` içindeki `_token_dogrula()` yine de `User.objects.filter(..., auth_token__key=token)` sorgusu yapıyor.

**Risk:**

- `authtoken` uygulaması yüklü olmadığı için `auth_token__key` filtresi `FieldError` veya boş sonuç döndürür; bu sessiz davranış güvenlik beklentisi ile gerçeklik arasında uçurum yaratır.
- Doğrulama fiilen yalnızca `_token_basit_dogrula()` üzerinden settings'teki sabit token'a düşüyor — single-key, rotate edilemez.
- Kimlik doğrulama davranışı gelecek bakımda sürpriz üretebilir.

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
