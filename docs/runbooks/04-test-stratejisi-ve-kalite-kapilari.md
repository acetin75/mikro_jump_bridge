# Runbook 04 — Test stratejisi ve kalite kapıları

**Faz:** P1  
**Durum:** Tespit edildi, uygulanmadı

## Amaç

Projeyi korkmadan değiştirebilmek için minimum güvence katmanını kurmak.

## Mevcut durum ve kanıtlar

### 1) Test kapsamı yok denecek kadar az

**Kanıtlar:**

- `kullanici/tests.py` yalnızca `from django.test import TestCase` içeriyor.
- `cari/`, `banka/`, `fatura/`, `gider/`, `kasa/`, `stok/`, `tahsilat/`, `ceksenet/` altında test dosyası görünmüyor.

**Risk:**

- Refactor korkutucu hale gelir.
- Finansal hesaplamalar sessizce bozulabilir.
- Rol/yetki kırılmaları fark edilmez.

### 2) Katkı sürecinde test zorunluluğu tanımlı değil

**Kanıt:**

- `CONTRIBUTING.md` içinde temel doğrulama olarak `python manage.py check` isteniyor.
- Test çalıştırma standardı tanımlı değil.

**Risk:**

- Kod kalitesi bireysel disipline kalır.

### 3) Kritik iş kuralları için regresyon ağı yok

**Örnek kritik alanlar:**

- `fatura/models.py` içindeki toplam ve KDV hesapları
- `fatura/views.py` içindeki fatura oluşturma akışı
- `muhasebe_buro/api_views.py` içindeki fatura aktarımı
- `kasa/utils.py` içindeki otomatik nakit hareketleri
- `muhasebe_buro/permissions.py` içindeki rol davranışları

## Hedef standart

- Her kritik modül için otomatik test paketi olmalı.
- Her PR öncesi çalıştırılan minimum kalite kapısı tanımlanmalı.
- İş kuralları sadece manuel tıklama ile doğrulanmamalı.

## Önerilen test matrisi

### Model testleri

- KDV ve toplam hesapları
- bakiye / property alanları
- negatif veya geçersiz veri kuralları

### View testleri

- yetki / login zorunluluğu
- başarılı POST → redirect + kayıt oluşumu
- hatalı POST → form tekrar gösterimi

### API testleri

- geçerli / geçersiz token
- eksik alanlar
- tekrar gönderim / mükerrer fatura
- rollback senaryosu

### Entegrasyon testleri

- fatura → cari hareket
- tahsilat / gider → kasa hareketi
- banka importu → hareket üretimi

## Kabul kriterleri

- Kritik akışlar için çalışan testler vardır.
- Test komutu standartlaştırılmıştır.
- Yeni hata bulunduğunda önce test eklenir, sonra düzeltme yapılır.

## Sonraki iş paketleri

- P1.4 — Test altyapısını kur
- P1.5 — Finansal çekirdek için ilk regresyon paketini yaz
- P1.6 — Yetki ve API testlerini ekle
