# Runbook 08 — Gözlemlenebilirlik, loglama ve denetim izi

**Faz:** P1  
**Durum:** Tespit edildi, kısmi altyapı var

## Amaç

Üretimde hata olduğunda “ne oldu, kimi etkiledi, hangi veri değişti?” sorularına dakikalar içinde yanıt verebilmek.

## Mevcut durum ve kanıtlar

### 1) Temel log altyapısı mevcut

**Kanıt:**

- `mikro_sync/settings.py` içinde dönen dosya logları tanımlı.

**Güçlü taraf:**

- Uygulama logu ve hata logu ayrılmış.
- Rotating file handler kullanılmış.

### 2) Aktivite logu çok sınırlı

**Kanıt:**

- `kullanici/models.py` içindeki `AktiviteLogu` sadece:
  - kullanıcı
  - tarih
  - URL yolu
  - IP
  bilgilerini tutuyor.

**Eksik olanlar:**

- hangi kayıt değişti
- eski / yeni değerler
- işlem tipi
- istek kimliği
- entegrasyon çağrısı korelasyonu

### 3) Yapısal log standardı yok

**Kanıt:**

- `settings.py` log formatı düz metin.
- request id / correlation id middleware bulunmuyor.

**Risk:**

- Çok adımlı hatalarda zinciri takip etmek zorlaşır.
- Destek ve inceleme süresi uzar.

### 4) Operasyon runbook'u yok

**Kanıt:**

- Repoda olay müdahalesi, hata ayıklama veya log inceleme kılavuzu bulunmuyor.

## Hedef standart

- Her kritik işlem izlenebilir olmalı.
- Kullanıcı veya entegrasyon kaynaklı değişiklikler denetlenebilir olmalı.
- Olay incelemesi için standart bir log sözleşmesi bulunmalı.

## Önerilen uygulama yaklaşımı

1. Request ID middleware ekle.
2. Kritik domain işlemlerini olay tipleriyle logla.
3. Audit trail için model değişiklik izini tasarla.
4. Kişisel veri ve sırların loglara sızmaması için maskeleme standardı ekle.
5. Operasyon ekibi için kısa müdahale prosedürü yaz.

## Kabul kriterleri

- Kritik yazma akışları için izlenebilir olay kayıtları vardır.
- Bir işlem tekil request id ile takip edilebilir.
- Audit kayıtları en azından hangi kaydın ne zaman kim tarafından değiştiğini gösterir.

## Sonraki iş paketleri

- P1.16 — Request correlation standardı
- P1.17 — Audit trail tasarımı
- P1.18 — Olay müdahale kılavuzu
