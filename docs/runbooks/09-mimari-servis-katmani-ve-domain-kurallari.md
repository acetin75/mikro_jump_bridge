# Runbook 09 — Mimari, servis katmanı ve domain kuralları

**Faz:** P2  
**Durum:** Tespit edildi, uygulanmadı

## Amaç

İş kurallarını view'lerden ayırarak projenin bakım maliyetini düşürmek ve test edilebilirliğini artırmak.

## Mevcut durum ve kanıtlar

### 1) View'lar hem HTTP hem domain mantığı taşıyor

**Kanıtlar:**

- `fatura/views.py` → form, formset, cari hareketi, kasa hareketi, durum geçişi aynı katmanda
- `gider/views.py` → kayıt + kasa etkisi aynı akışta
- `cari/views.py` → hareket oluşturma ve mutabakat hesaplaması view içinde

### 2) Domain yan etkileri yardımcı fonksiyonlara dağılmış

**Kanıt:**

- `kasa/utils.py` içinde tahsilat, gider ve fatura için kasa hareketi üretimi var.
- Bu fonksiyonlar servis sözleşmesi olmadan çeşitli view'lerden çağrılıyor.

### 3) Model seviyesinde doğrulama zayıf

**Kanıt:**

- `fatura/models.py` içinde `clean()` veya ek doğrulama mekanizması yok.
- Tutar, vade, iş kuralı ilişkileri model seviyesinde merkezileştirilmemiş.

### 4) Hesaplamalar dağınık

**Kanıtlar:**

- `gider/views.py` toplamları Python tarafında döngü ile hesaplıyor.
- `dashboard/views.py` bazı toplamları yine Python `sum(...)` ile hesaplıyor.
- Bu yaklaşım küçük veri için çalışır; büyüyen veri için bakım ve performans riski taşır.

## Hedef standart

- View sadece istek/yanıt orkestrasyonu yapmalı.
- Domain kararları servis katmanında toplanmalı.
- Model doğrulamaları merkezi ve test edilebilir olmalı.

## Önerilen uygulama yaklaşımı

1. Finansal işlemler için servis katmanı çıkar:
   - `FaturaService`
   - `TahsilatService`
   - `GiderService`
   - `BankaImportService`
2. Durum geçişleri için açık domain kuralları tanımla.
3. Model `clean()` ve servis doğrulamalarını birlikte kullan.
4. Hesaplama stratejilerini gerektiğinde query / annotation seviyesine taşı.

## Kabul kriterleri

- Kritik iş kuralları view içinde dağınık kalmaz.
- Domain işlemleri bağımsız test edilebilir hale gelir.
- Yeni özellik eklemek için mevcut view'leri kopyala-yapıştır ihtiyacı azalır.

## Sonraki iş paketleri

- P2.2 — Finansal servis katmanı tasarımı
- P2.3 — Domain doğrulama sözleşmesi
- P2.4 — View sadeleştirme refactor'u
