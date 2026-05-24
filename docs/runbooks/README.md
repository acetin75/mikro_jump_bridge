# Mikro Jump Bridge — Runbook Seti

Bu klasör, proje için **olmazsa olmaz eksikliklerin** fazlı ve uygulanabilir dökümünü içerir.
Amaç; sonraki oturumlarda her başlığı tek tek ele alıp tasarlamak, iyileştirmek, uygulamak ve doğrulamaktır.

> **Son güncelleme:** 2026-05-24  
> **Versiyon:** v0.5 — 18 runbook, mikro_jump_bridge'e özgü

## İnceleme özeti

İnceleme alanları:

- Copilot / AI ile geliştirme yönetişimi
- Altyapı ve operasyonel hazırlık
- Mimari ve sürdürülebilirlik
- Kod kalitesi ve kalite kapıları
- Güvenlik, yetki ve veri bütünlüğü
- Yasal uyum (KVKK) ve veri saklama
- Performans ve entegrasyon dayanıklılığı
- Modüler yapı ve kod boyut standartları
- Frontend disiplini ve tasarım sistemi

## Mevcut güçlü yönler

Projede eksiklerden önce teslim edilmiş bazı sağlam parçalar da var:

- `.github/copilot-instructions.md` detaylı ve proje bağlamı güçlü.
- `pyproject.toml` içinde `ruff` yapılandırması mevcut.
- `mikro_sync/settings.py` içinde dönen dosya loglama altyapısı var.
- `mikro_sync/middleware.py` login + firma seçim + lisans zorunluluğu çerçevesi sağlıyor.
- `lisans/` app ile HMAC-SHA256 imzalı 15 günlük deneme + anahtar aktivasyon altyapısı tamam.
- `sync_motor/client.py` içinde MD5 günlük hash auth ile güvenli Mikro ERP bağlantısı.
- `mikro_gelen/` staging alanı — ham fatura verisi `ham_json`'da korunuyor, durum makinesi var.
- Kökte `.env.example` mevcut — yerel kurulum için iyi bir referans.

## Kritik boşluklar — faz ve durum tablosu

| #  | Faz | Öncelik | Durum    | Başlık |
|----|-----|---------|----------|--------|
| 01 | P0  | Kritik  | ✅ Tamam  | Güvenlik, sır yönetimi ve ilk kurulum güvenliği |
| 02 | P0  | Kritik  | 🟡 Kısmi | Kimlik doğrulama, yetkilendirme ve API güvenliği |
| 03 | P1  | Yüksek  | ⛔ Açık  | Veri bütünlüğü ve transaction standardı |
| 04 | P1  | Yüksek  | ⛔ Açık  | Test stratejisi ve kalite kapıları |
| 05 | P1  | Yüksek  | ⛔ Açık  | CI/CD ve otomasyon standardı |
| 06 | P1  | Yüksek  | ⛔ Açık  | Bağımlılık ve tekrarlanabilir kurulum |
| 07 | P1  | Yüksek  | 🟡 Kısmi | Yedekleme, geri yükleme ve felaket kurtarma |
| 08 | P1  | Yüksek  | 🟡 Kısmi | Gözlemlenebilirlik, loglama ve denetim izi |
| 09 | P2  | Orta    | ⛔ Açık  | Mimari, servis katmanı ve domain kuralları |
| 10 | P2  | Orta    | 🟡 Kısmi | Copilot yönetişimi ve geliştirme protokolü |
| 11 | P1  | Yüksek  | ⛔ Açık  | KVKK, kişisel veri ve veri saklama |
| 12 | P2  | Orta    | ⛔ Açık  | Performans, sorgu optimizasyonu ve ölçeklenebilirlik |
| 13 | P1  | Yüksek  | ⛔ Açık  | Mikro Sync entegrasyon dayanıklılığı ve hata yönetimi |
| 14 | P2  | Orta    | ⛔ Açık  | Modülerlik ve kod boyut standartları |
| 15 | P2  | Orta    | ⛔ Açık  | Frontend disiplini ve tasarım sistemi |
| 16 | P1  | Aktif   | ✅ Tamam  | Kod kalitesi araçları ve Git/Copilot geliştirme protokolü |
| 17 | P1  | Yüksek  | ⛔ Açık  | Bağımlılık güncelleme ve uyumluluk |
| 18 | P1  | Yüksek  | ✅ Tamam  | PDF/Excel Türkçe karakter standardı |

**Durum lejantı:**  
⛔ Açık — tespit edildi, çalışılmadı &nbsp;•&nbsp; 🟡 Kısmi — bir kısmı mevcut, eksikler var &nbsp;•&nbsp; ✅ Tamam — kabul kriterleri karşılandı

## Dosya haritası

1. [01-guvenlik-sir-yonetimi-ve-kurulum-guvenligi.md](01-guvenlik-sir-yonetimi-ve-kurulum-guvenligi.md)
2. [02-kimlik-dogrulama-yetkilendirme-ve-api-guvenligi.md](02-kimlik-dogrulama-yetkilendirme-ve-api-guvenligi.md)
3. [03-veri-butunlugu-ve-transaction-standardi.md](03-veri-butunlugu-ve-transaction-standardi.md)
4. [04-test-stratejisi-ve-kalite-kapilari.md](04-test-stratejisi-ve-kalite-kapilari.md)
5. [05-ci-cd-ve-otomasyon-standardi.md](05-ci-cd-ve-otomasyon-standardi.md)
6. [06-bagimlilik-ve-tekrarlanabilir-kurulum.md](06-bagimlilik-ve-tekrarlanabilir-kurulum.md)
7. [07-yedekleme-geri-yukleme-ve-felaket-kurtarma.md](07-yedekleme-geri-yukleme-ve-felaket-kurtarma.md)
8. [08-gozlemlenebilirlik-loglama-ve-denetim-izi.md](08-gozlemlenebilirlik-loglama-ve-denetim-izi.md)
9. [09-mimari-servis-katmani-ve-domain-kurallari.md](09-mimari-servis-katmani-ve-domain-kurallari.md)
10. [10-copilot-yonetisimi-ve-gelistirme-protokolu.md](10-copilot-yonetisimi-ve-gelistirme-protokolu.md)
11. [11-kvkk-ve-kisisel-veri-saklama.md](11-kvkk-ve-kisisel-veri-saklama.md)
12. [12-performans-ve-olceklenebilirlik.md](12-performans-ve-olceklenebilirlik.md)
13. [13-mikro-sync-entegrasyon-dayanikliligi.md](13-mikro-sync-entegrasyon-dayanikliligi.md)
14. [14-modulerlik-ve-kod-boyut-standartlari.md](14-modulerlik-ve-kod-boyut-standartlari.md)
15. [15-frontend-disiplini-ve-tasarim-sistemi.md](15-frontend-disiplini-ve-tasarim-sistemi.md)
16. [16-kod-kalitesi-ve-git-copilot-protokolu.md](16-kod-kalitesi-ve-git-copilot-protokolu.md)
17. [17-bagimlilik-guncelleme-ve-uyumluluk.md](17-bagimlilik-guncelleme-ve-uyumluluk.md)
18. [18-pdf-excel-turkce-karakter-standardi.md](18-pdf-excel-turkce-karakter-standardi.md)

## Uygulama sırası önerisi

1. **P0 (kritik) kapatılmalı:** 01, 02 — güvenlik ve yetki.
2. **P1 (yüksek) tamamlanmalı:** 03, 04, 05, 06, 07, 08, 11, 13, 16, 17, 18 — transaction, test, CI, bağımlılık, kurtarma, gözlem, KVKK, entegrasyon, kalite, güncelleme, PDF.
3. **P2 (orta) ile bakım maliyeti düşürülmeli:** 09, 10, 12, 14, 15 — mimari, süreç, performans, modülerlik, frontend.

## Runbook formatı

Tüm runbook'lar şu standart bölümleri içerir:

- **Faz / Durum** — fazlama ve mevcut ilerleme.
- **Amaç** — bu başlık neden var.
- **Mevcut durum ve kanıtlar** — kod referansları, dosya/satır kanıtı.
- **Hedef standart** — ulaşılmak istenen son hâl.
- **Önerilen uygulama yaklaşımı** — adım adım yol haritası.
- **Kabul kriterleri** — "tamam" demek için karşılanması gereken ölçütler.
- **Sonraki iş paketleri** — daha küçük takip görevleri.

## Konfigürasyon notu

Proje ortam değişkenleri kullandığı için kökte `.env.example` şablon dosyası bulunur.
Yerel kurulumda bu dosya `.env` olarak kopyalanıp değerler doldurulmalıdır.
`.env` dosyası repoya **commit edilmez** ve üretim sırları kesinlikle `.env.example` içine yazılmaz.
