# Runbook 10 — Copilot yönetişimi ve geliştirme protokolü

**Faz:** P2  
**Durum:** Tespit edildi, iyi başlangıç var

## Amaç

Copilot destekli geliştirmeyi rastgele öneri üretiminden çıkarıp, proje standardına bağlı ve denetlenebilir bir üretim akışına dönüştürmek.

## Mevcut durum ve kanıtlar

### 1) Güçlü proje talimatı mevcut

**Kanıt:**

- `.github/copilot-instructions.md` kapsamlı, proje odaklı ve değerli.

**Güçlü taraf:**

- teknoloji yığını
- app standartları
- model / view / form / URL / template kuralları
- loglama ve güvenlik notları

### 2) Fakat Copilot için operasyonel geliştirme protokolü eksik

**Kanıtlar:**

- `.github/` altında yalnızca `copilot-instructions.md` var.
- Kökte `AGENTS.md` (modern AI ajan sözleşmesi) bulunmuyor; çoklu ajan / araç senaryolarında ortak protokol eksik.
- Faz bazlı backlog, görev şablonu, definition of done veya risk sınıflama dokümanı yok.
- `CONTRIBUTING.md` içinde AI destekli değişikliklere özel kalite kuralları tanımlı değil.
- `.github/PULL_REQUEST_TEMPLATE.md` ve `ISSUE_TEMPLATE/` klasörleri yok.

### 3) AI katkısının kaliteye bağlandığı zorunlu kapılar yok

**Kanıtlar:**

- CI yok.
- Test standardı yok.
- Mimari karar kayıtları yok.

**Risk:**

- Copilot çıktısı tutarlı olsa bile proje hafızasına dönüşmeyebilir.
- Aynı tip hatalar tekrar üretilebilir.

## Hedef standart

- Copilot her değişiklikte aynı karar çerçevesini kullanmalı.
- AI destekli değişiklikler için “önce analiz, sonra test, sonra uygulama” disiplini belgelenmeli.
- Faz bazlı teknik borç ve standart dışı alanlar kayıt altında tutulmalı.

## Önerilen uygulama yaklaşımı

1. Bu runbook setini yaşayan backlog olarak kullan.
2. Her geliştirme için küçük bir görev şablonu tanımla:
   - amaç
   - etkilenen dosyalar
   - risk seviyesi
   - test etkisi
   - rollback planı
3. Mimari kararlar için ADR klasörü ekle.
4. `CONTRIBUTING.md` içine AI destekli değişikliklerin asgari doğrulama adımlarını ekle.
5. Faz bazlı ilerleme tablosu tut.

## Kabul kriterleri

- Yeni görevler runbook veya ADR ile ilişkilendirilir.
- AI ile yapılan değişiklikler standart kalite kapılarından geçer.
- Teknik borç ve istisnalar görünür bir backlog içinde yaşar.

## Sonraki iş paketleri

- P2.5 — ADR ve görev şablonu standardı
- P2.6 — Copilot destekli teslim kontrol listesi
- P2.7 — Faz takip tablosu ve ownership modeli
