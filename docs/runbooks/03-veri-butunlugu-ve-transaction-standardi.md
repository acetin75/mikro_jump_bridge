# Runbook 03 — Veri bütünlüğü ve transaction standardı

**Faz:** P1
**Durum:** ⛔ Açık — tespit edildi, uygulanmadı

## Amaç

Import pipeline ve staging işlemlerinde birden fazla kayıt oluştuğunda işlemin ya tamamen başarılı ya da tamamen geri alınmış olmasını sağlamak.

---

## Mevcut durum ve kanıtlar

### 1) Import pipeline transaction korumasız çalışıyor

**Kanıt:**

- `sync_motor/views.py` → `import_baslat()` içinde:
  - `ImportLog.save()` (durum: isleniyor)
  - Mikro API çağrısı → her `MikroFatura` için `save()`
  - `ImportLog.save()` (durum: tamamlandi / hata)
- Döngü ortasında exception oluşursa `ImportLog` eski durumda kalır, yarım kaydedilmiş `MikroFatura` satırları temizlenmez.

**Risk:**

- Ağ/API hatası sonrası import yeniden çalıştırıldığında `fat_guid` unique kısıtına çarpar.
- `ImportLog.cekilen_adet` ve `aktarilan_adet` gerçeği yansıtmaz.

### 2) MikroFatura durum geçişleri korunmasız

**Kanıt:**

- `mikro_gelen/views.py` → fatura durum güncelleme (`ham` → `islendi` / `atla`) sırasında `transaction.atomic()` yok.
- Durum değişikliği başarılı olsa bile bağlı başka bir kayıt güncellemesi başarısız olursa tutarsızlık oluşur.

### 3) Toplu aktarım döngüsü atomik değil

**Kanıt:**

- `sync_motor/client.py` içindeki `fatura_aktar()` her fatura için ayrı HTTP isteği yapar.
- Başarılı aktarım sonrası `ImportLog.aktarilan_adet` artışı ayrı bir `save()` ile yapılır.
- Sayaç ile gerçek aktarım arasında uçurum oluşabilir.

---

## Hedef standart

- Import döngüsünün her bir birimi (tek fatura aktarımı + log sayaç güncellemesi) `transaction.atomic()` altında olmalı.
- `ImportLog` durum güncellemeleri tutarlı ve geri alınabilir olmalı.
- Toplu insert'lerde `bulk_create(ignore_conflicts=True)` kullanılmalı.

---

## Önerilen uygulama yaklaşımı

1. `sync_motor/views.py` → `import_baslat()` içinde her fatura döngüsünü `with transaction.atomic():` ile sar.
2. `MikroFatura` toplu ekleme varsa `MikroFatura.objects.bulk_create(liste, ignore_conflicts=True)` kullan.
3. `ImportLog` durum güncellemesini `update_fields=["durum", "aktarilan_adet", "hata_adet", "guncellendi"]` ile minimize et.
4. Hata durumunda `ImportLog.durum = "hata"` + `logger.error(...)` birlikte atomik kaydet.

---

## Kabul kriterleri

- Import döngüsü yarıda kesilirse DB tutarlı kalır.
- Yeniden çalıştırılan import, yarım kalan kayıtları temiz işler.
- `ImportLog.aktarilan_adet + hata_adet == cekilen_adet` her zaman sağlanır.

---

## Sonraki iş paketleri

- P1.1 — `import_baslat()` view'ında transaction koruması
- P1.2 — `MikroFatura` toplu insert standardı
- P1.3 — `ImportLog` sayaç güncellemesi güvencesi
