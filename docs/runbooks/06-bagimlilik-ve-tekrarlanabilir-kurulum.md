# Runbook 06 — Bağımlılık ve tekrarlanabilir kurulum

**Faz:** P1  
**Durum:** Tespit edildi, uygulanmadı

## Amaç

Aynı repo farklı günlerde ve farklı makinelerde aynı şekilde kurulabilmeli ve aynı davranışı vermeli.

## Mevcut durum ve kanıtlar

### 1) Bağımlılıklar gevşek aralıklarla tanımlı

**Kanıtlar:**

- `requirements.txt` içinde çoğu paket `>=` ile tanımlı.
- `requirements-dev.txt` de sabit sürüm kilidi içermiyor.

**Risk:**

- Bugün çalışan kurulum yarın farklı alt sürümle bozulabilir.
- Hata tekrar üretmek zorlaşır.

### 2) Kilit dosyası yok

**Kanıt:**

- Repoda `requirements-lock.txt`, `poetry.lock`, `uv.lock` veya benzeri lock dosyası bulunmuyor.

### 3) Ortam bağımlılığı yüksek

**Kanıt:**

- `mikro_sync/settings.py` `python-decouple` gerektiriyor.
- Bu inceleme sırasında sistem Python ile `python manage.py check` çalıştırıldığında `ModuleNotFoundError: No module named 'decouple'` alındı.
- Bu durum proje komutlarının venv dışı kullanımda kolayca bozulduğunu gösteriyor.

### 4) `.env` üretim akışı belirsiz

**Kanıt:**

- Kökte yalnızca `.env.example` mevcut, gerçek `.env` repoda yok (olmamalı).
- `baslat.bat` ilk çalıştırmada `.env` yokluğunu tespit edip kullanıcıyı yönlendirmiyor.
- `KURULUM.md` içinde `copy .env.example .env` adımı net bir checklist olarak vurgulanmamış.

**Risk:**

- Yeni kurulan makinede `SECRET_KEY` placeholder kalır, sistem güvensiz varsayılanlarla açılır (bkz. runbook 01).

## Hedef standart

- Üretim ve geliştirme bağımlılıkları kararlı sürümlere sabitlenmeli.
- Kurulum tek komutla ve öngörülebilir olmalı.
- Geliştirici makinesi ile CI aynı bağımlılık setini kullanmalı.

## Önerilen uygulama yaklaşımı

1. Test edilmiş bağımlılıkları sabit sürümlere kilitle.
2. Ayrı lock dosyası veya modern paket yöneticisi kullan.
3. Standart çalışma komutlarını `.venv` ve aktif ortamla uyumlu hale getir.
4. Geliştirme ve üretim bağımlılıklarını net ayır.

## Kabul kriterleri

- Aynı commit farklı makinelerde aynı bağımlılık sürümleriyle kurulur.
- CI ve yerel ortam aynı lock setini kullanır.
- Kurulum sonrası temel doğrulama komutları dokümante edildiği şekilde çalışır.

## Sonraki iş paketleri

- P1.10 — Lock stratejisini seç
- P1.11 — Bağımlılıkları sabitle
- P1.12 — Kurulum/doğrulama dokümantasyonunu eşitle
