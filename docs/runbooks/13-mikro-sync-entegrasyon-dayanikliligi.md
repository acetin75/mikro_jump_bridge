# Runbook 13 — Mikro Sync entegrasyon dayanıklılığı ve hata yönetimi

**Faz:** P1  
**Durum:** Tespit edildi, uygulanmadı

## Amaç

Muhasebe Bürosu ↔ Mikro ERP (8001 portundaki `mikro_sync` köprüsü) entegrasyonu, ağ/ERP/parser hatalarına karşı **öngörülebilir** ve **veri kaybetmeden** davranmalı.

> **Bağlantılı runbook'lar:** 02 (API güvenliği), 03 (transaction), 08 (gözlemlenebilirlik).

## Mevcut durum ve kanıtlar

### 1) Hata yanıt sözleşmesi belirsiz

**Kanıt:**

- `muhasebe_buro/api_views.py` → `fatura_aktar()` farklı hata durumlarında farklı JSON şekilleri döndürebiliyor:
  - `{"hata": "..."}`
  - `{"durum": "mevcut", "fatura_id": N}`
  - `{"durum": "ok", "fatura_id": N}`
- HTTP kodları tutarsız (200 / 400 / 401), gövde şeması tanımlı değil.

**Risk:**

- `mikro_sync` istemcisi hatayı yanlış sınıflandırır; retry kararı belirsiz olur.

### 2) Retry / circuit breaker yok

**Kanıt:**

- `mikro_sync` tarafında `MuhasebeBuroClient` ağ hatasında otomatik yeniden deneme yapmıyor (varsayılan davranış).
- Geçici hata (timeout, 5xx) ile kalıcı hata (400 validation) ayrımı yok.

**Risk:**

- Anlık ERP bağlantı kopması = tüm aktarım batch'inin kaybı.

### 3) İdempotency anahtarı zayıf

**Kanıt:**

- Çağıran taraf `fat_guid` gönderiyor; ancak Muhasebe Bürosu tarafında `Fatura` modelinde bu alana karşılık gelen **unique alan veya index** yok (kontrol edilmeli).
- Tekrar gönderim için sorgu fatura_no üzerinden yapılıyor → numaralar farklı yıllarda çakışabilir.

**Risk:**

- Aynı `fat_guid` ile farklı `fatura_no` gönderiminde mükerrer kayıt.
- Yıllar arası `fatura_no` çakışmasında yanlış "mevcut" kararı.

### 4) Kısmi başarı senaryosu yönetilmiyor

**Kanıt:**

- Çoklu satır içeren bir faturada ortada hata olursa (runbook 03'te de tespit edildi) yarım kayıt kalabilir.
- `mikro_sync` tarafında `ImportLog` tablosu var; ancak failure detail/stacktrace zenginliği belirsiz.

### 5) İzlenebilirlik zayıf

**Kanıt:**

- API çağrılarına `X-Request-Id` veya correlation header beklenmiyor.
- `logs/uygulama.log` içinde Mikro çağrılarını tek string ile takip etmek zor.
- Webhook / push modu yok; iki yönlü değişiklik bildirimi pull modunda gerçekleşir.

### 6) Sürüm uyumsuzluğu için kontrol yok

**Kanıt:**

- API endpoint'leri `/api/v1/` prefix'ine sahip ama versiyon negotiation veya sunucu sürüm beyanı yok.
- `mikro_sync` istemcisi farklı bir muhasebe_buro sürümüne karşı çalıştığında bunu anlayamaz.

### 7) Şifreleme stratejisi yalnızca Mikro şifresi için

**Kanıt:**

- `mikro_sync` tarafında `FirmaAyar.sifre_kaydet/sifre_al` mevcut (`django.core.signing.Signer`).
- `Signer` **şifreleme değil imzalamadır** — DB erişimi olan biri şifreyi okuyabilir.

**Risk:**

- DB sızıntısında Mikro şifreleri ele geçer.

## Hedef standart

- Tüm API yanıtları aynı şemayı kullanır: `{"ok": bool, "code": "...", "message": "...", "data": {...}}`.
- HTTP kodları davranışa eşlenmiştir (200, 201, 400, 401, 409, 422, 5xx).
- Geçici hatalar **idempotent retry + exponential backoff** ile karşılanır.
- Aktarımlar `fat_guid` üzerinden **DB-level unique constraint** ile idempotenttir.
- Her isteğin **correlation id**'si vardır ve iki tarafın logunda bulunur.
- Mikro şifreleri **gerçek şifreleme** ile saklanır (Fernet/AES-GCM).

## Önerilen uygulama yaklaşımı

1. **Yanıt sözleşmesini sabitle:** `muhasebe_buro/api_views.py` için ortak `api_yanit(ok, code, message, data, status)` yardımcısı yaz.
2. **Hata kodu kataloğu:** `docs/api/hata-kodlari.md` — `AUTH_INVALID`, `VALIDATION_FAILED`, `DUPLICATE_GUID`, `INTERNAL`...
3. **Idempotency:** `Fatura` modeline `mikro_guid = CharField(unique=True, null=True, blank=True)` ekle; aktarımda `update_or_create(mikro_guid=...)`.
4. **Retry stratejisi:** `mikro_sync/client.py` içinde `tenacity` veya elle yazılmış backoff (1s, 3s, 10s, vazgeç).
5. **Correlation id:** `X-Request-Id` başlığını her iki tarafta middleware ile log'a yaz (runbook 08 ile birleşik).
6. **Kısmi başarı için outbox/staging:** Mikro aktarımları önce `mikro_gelen/MikroFatura` staging'ine al, sonra atomic transaction ile Muhasebe Bürosu kayıtlarına işle.
7. **API versiyon negotiation:** `/api/v1/ping/` yanıtında `{"server_version": "...", "api_versions": ["v1"]}` döndür.
8. **Şifreleme güçlendir:** `FirmaAyar` şifre saklamayı `cryptography.fernet.Fernet` ile yeniden yaz; anahtar `.env` üzerinden gelir.
9. **Health check:** `/api/v1/health/` — DB, disk, son başarılı aktarım zamanı.

## Kabul kriterleri

- Tüm API yanıtları aynı şemaya uyar (sözleşme testi vardır).
- Aynı `fat_guid` ile 10 kez aktarım denendiğinde DB'de tek kayıt olur.
- Mikro tarafı 503 alırsa otomatik retry yapar, başarısızsa `ImportLog`'a kalıcı hata yazar.
- İki taraf logunda aynı `request_id` ile bir aktarımı uçtan uca takip etmek mümkündür.
- `FirmaAyar.sifre_al()` çıktısı imzalama değil şifre çözmedir; DB erişimi tek başına şifreyi açığa çıkarmaz.

## Sonraki iş paketleri

- P1.21 — API yanıt sözleşmesini sabitle + hata kataloğu
- P1.22 — `mikro_guid` unique + idempotent upsert
- P1.23 — Retry + correlation id
- P1.24 — Mikro şifre gerçek şifreleme
- P2.12 — Versiyon negotiation + health endpoint
