# Runbook 07 — Yedekleme, geri yükleme ve felaket kurtarma

**Faz:** P1  
**Durum:** Tespit edildi, kısmi altyapı var

## Amaç

Veri kaybı veya bozulma anında sistemin nasıl ayağa kaldırılacağını prosedüre bağlamak.

## Mevcut durum ve kanıtlar

### 1) Temel yedek alma yaklaşımı var, fakat prosedür eksik

**Kanıtlar:**

- `README.md` ve `KURULUM.md` içinde `db.sqlite3` kopyalama yaklaşımı anlatılıyor.
- `dashboard/views.py` içinde `yedek_indir()` ve `yedek_yukle()` fonksiyonları bulunuyor.

**Güçlü taraf:**

- Yedek indir / yükle için başlangıç seviyesinde işlev mevcut.

### 2) Kurtarma standardı dokümante değil

**Eksik başlıklar:**

- yedek alma sıklığı
- saklama süresi
- yedeğin ikinci lokasyonda tutulması
- `media/` klasörünün dahil edilip edilmeyeceği
- geri yükleme sonrası doğrulama adımları
- rollback stratejisi

### 3) Geri yükleme riskleri ele alınmamış

**Kanıt:**

- `dashboard/views.py` içindeki `yedek_yukle()` doğrudan `db.sqlite3` üzerine yazıyor.
- Dosya doğrulama, bütünlük kontrolü ve bakım modu akışı yok.

**Risk:**

- Yanlış veya bozuk yedek sisteme yüklenebilir.
- Canlı kullanım sırasında dosya değişimi veri kaybına yol açabilir.

## Hedef standart

- RPO/RTO tanımlı olmalı.
- Yedek alma, saklama, geri yükleme ve doğrulama adımları net olmalı.
- Operasyon kişiye bağlı olmadan tekrar edilebilir olmalı.

## Önerilen uygulama yaklaşımı

1. Yedek kapsamını tanımla: `db.sqlite3`, `media/`, gerekiyorsa dışa aktarım dosyaları.
2. Geri yükleme öncesi bakım modu veya servis durdurma standardı koy.
3. Yedek dosyası doğrulama ve hash kontrolü ekle.
4. Kurtarma tatbikatı prosedürü yaz.
5. UI geri yükleme akışı için yetki, doğrulama ve log detayını artır.

## Kabul kriterleri

- Tekrarlanabilir bir geri yükleme prosedürü yazılıdır.
- Örnek kurtarma tatbikatı başarıyla uygulanmıştır.
- Yedek geri yükleme sonrası doğrulama checklist'i vardır.

## Sonraki iş paketleri

- P1.13 — Backup/restore SOP yaz
- P1.14 — Güvenli geri yükleme akışını sertleştir
- P1.15 — Tatbikat ve doğrulama kayıtlarını ekle
