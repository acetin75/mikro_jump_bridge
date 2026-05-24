# Runbook 03 — Veri bütünlüğü ve transaction standardı

**Faz:** P0  
**Durum:** 🟡 Kısmi (2026-05-23) — transaction koruması eklendi; servis katmanı P2'de

### Yapılan değişiklikler

| Dosya | Değişiklik |
|---|---|
| `fatura/views.py` | `fatura_ekle()` ve `fatura_durum_degistir()` — `transaction.atomic()` eklendi |
| `tahsilat/views.py` | `tahsilat_ekle()` — `transaction.atomic()` eklendi |
| `gider/views.py` | `gider_ekle()` — `transaction.atomic()` eklendi |
| `banka/views.py` | `ekstre_yukle()` — hareket döngüsü + ekstre.islendi kaydı `transaction.atomic()` eklendi |

**Açık kalan:** Domain servislerine taşıma (runbook 09, P2).

## Amaç

Bir iş akışında birden fazla kayıt oluşuyorsa, işlemin ya tamamen başarılı ya da tamamen geri alınmış olması gerekir. Bu runbook veri bütünlüğünü o standarda taşımayı hedefler.

## Mevcut durum ve kanıtlar

### 1) Fatura oluşturma çok adımlı ama transaction koruması yok

**Kanıt:**

- `fatura/views.py` → `fatura_ekle()` içinde:
  - `form.save()`
  - `formset.save()`
  - `_cari_hareket_ekle(fatura)`
- Akışta `transaction.atomic` yok.

**Risk:**

- Fatura oluşup kalemler veya cari hareket oluşmazsa finansal kayıtlar sapar.
- Yarım kayıtlar işletme verisini bozar.

### 3) Banka ekstre parse akışında toplu kayıtlar transaction dışında

**Kanıt:**

- `banka/views.py` → `ekstre_yukle()` içinde `BankaEkstre` kaydı ve ardından `for satir in satirlar` ile `BankaHareketi.objects.create(...)`
- Akışta transaction yok.

**Risk:**

- Ekstre işlendi bilgisi ile üretilen hareket sayısı birbirinden kopabilir.
- Kısmi import tekrar çalıştırmalarda mükerrer kayıt üretebilir.

### 4) Tahsilat oluşturma çok adımlı ama transaction koruması yok

**Kanıt:**

- `tahsilat/views.py` → `tahsilat_ekle()` içinde sırasıyla:
  - `form.save()` ile `Tahsilat` kaydı
  - `HesapHareketi.objects.create(...)` ile cari hareketi
  - `tahsilat_kasa_hareketi_olustur(t)` ile (nakit ise) kasa hareketi
- Akışta `transaction.atomic` yok.

**Risk:**

- Cari bakiyesi tahsilat kaydı ile uyumsuz kalabilir.
- Nakit kasa hareketinde hata olursa tahsilat kaydı yarım kayıt olarak sistemde durur.

### 5) Domain etkileri view içinde dağınık

**Kanıtlar:**

- `fatura/views.py` → `_cari_hareket_ekle(fatura)`
- `gider/views.py` → `gider_kasa_hareketi_olustur(gider)`
- `fatura/views.py` → `fatura_kasa_hareketi_olustur(fatura)`
- `kasa/utils.py` → finansal yan etkiler ayrı yardımcı fonksiyonlarda

**Risk:**

- Aynı domain kuralı birden fazla yerde çağrılabilir veya unutulabilir.
- Test etmek zorlaşır.

## Hedef standart

- Çok kayıtlı tüm yazma operasyonları atomik olmalı.
- İdempotent entegrasyon akışları tanımlanmalı.
- Finansal yan etkiler servis katmanında tek noktada toplanmalı.

## Önerilen uygulama yaklaşımı

1. Çok adımlı tüm create/update akışlarını envanterle.
2. `transaction.atomic` ile koru.
3. Tekrarlı import senaryoları için idempotency anahtarları belirle.
4. Finansal yan etkileri servis katmanına taşı.
5. Veri bütünlüğü için hata durumlarında rollback testleri ekle.

## Kabul kriterleri

- Fatura, gider, tahsilat, banka importu gibi çok adımlı işlemlerde yarım kayıt bırakan senaryo kalmaz.
- Aynı entegrasyon payload'ı tekrar gönderildiğinde sistem tutarlı davranır.
- Kritik yazma akışları transaction testleriyle doğrulanır.

## Sonraki iş paketleri

- P0.5 — Kritik yazma akışlarını atomik hale getir (fatura, gider, tahsilat, banka import, API fatura aktarımı)
- P1.3 — İdempotent import davranışı ekle (banka ekstre + Mikro fatura aktarımı için unique constraint + `update_or_create`)
- P2.1 — Domain servisleri ile yan etkileri merkezileştir (bkz. runbook 09)
