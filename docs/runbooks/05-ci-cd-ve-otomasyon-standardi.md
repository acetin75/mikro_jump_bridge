# Runbook 05 — CI/CD ve otomasyon standardı

**Faz:** P1  
**Durum:** Tespit edildi, uygulanmadı

## Amaç

Kalite kontrollerinin kişiye bağlı değil, otomatik çalışan bir boru hattına bağlanması.

## Mevcut durum ve kanıtlar

### 1) GitHub Actions / CI pipeline yok

**Kanıt:**

- `.github/workflows/` klasörü bulunmuyor.

**Risk:**

- Lint ve testler PR seviyesinde otomatik çalışmıyor.
- Bozuk kodun ana dala alınma ihtimali artıyor.

### 2) Kalite kapıları sadece dokümantasyonda anılıyor

**Kanıtlar:**

- `README.md` ve `CONTRIBUTING.md` içinde `ruff` ve `manage.py check` komutları yazıyor.
- Bunları zorunlu kılan pipeline veya hook seti yok.

### 3) Yayın / paketleme standardı tanımlı değil

**Kanıtlar:**

- Release rozeti mevcut fakat dağıtım workflow'u görünmüyor.
- Migration, lint, test ve sürümleme zinciri otomasyonla güvenceye alınmamış.

## Hedef standart

- Her push ve PR için otomatik doğrulama çalışmalı.
- Lint, test, Django check ve güvenlik denetimleri standardize edilmeli.
- Versiyonlama ve release akışı tekrar üretilebilir hale gelmeli.

## Önerilen minimum pipeline

1. Bağımlılık kurulumu
2. `ruff check .`
3. test komutu
4. `python manage.py check`
5. isteğe bağlı: `python manage.py check --deploy`

## Genişletilmiş hedef

- pre-commit kancaları
- bağımlılık güvenlik taraması
- sürüm etiketi oluşturma disiplini
- changelog üretimi

## Kabul kriterleri

- Yeni workflow dosyaları repoda yer alır.
- Başarısız lint/test durumunda PR geçemez.
- Pipeline yerel ve uzak ortamda aynı kalite kapılarını uygular.

## Sonraki iş paketleri

- P1.7 — İlk CI workflow'unu kur
- P1.8 — Branch koruma kurallarını tanımla
- P1.9 — pre-commit standardı ekle
