# Runbook 12 — Performans, sorgu optimizasyonu ve ölçeklenebilirlik

**Faz:** P2  
**Durum:** Tespit edildi, uygulanmadı

## Amaç

Veri büyüdükçe (binlerce fatura, on binlerce hareket) sayfaların açılma süresi ve raporların üretim süresi öngörülebilir kalmalı.
SQLite + tek kullanıcı modelinde bile performans sessizce bozulabilir.

## Mevcut durum ve kanıtlar

### 1) Python tarafında toplulaştırma

**Kanıtlar:**

- `dashboard/views.py` (214 satır) — bazı toplamlar `sum(...)` ile Python tarafında hesaplanıyor.
- `gider/views.py` — KDV ve toplam tutarlar QuerySet üzerinde döngüyle hesaplanıyor.
- `rapor/views.py` (318 satır) — dönem özetleri Python `for` ile birleştiriliyor.

**Risk:**

- N kayıt için N sorgu veya tüm tabloyu RAM'e çekme.
- Veritabanı `SUM()`, `Count()`, `Coalesce` agregasyonları kullanılmıyor.

### 2) N+1 sorgu riski

**Kanıt:**

- Bazı view'larda `select_related` / `prefetch_related` kullanılmış (iyi); ancak `templates/fatura/detail.html`, `templates/cari/detail.html` gibi sayfalarda template içinde `{% for kalem in fatura.kalemler.all %}` döngüleri görülüyor.
- Template'te `.all` çağrısı view'da `prefetch_related("kalemler")` yapılmamışsa N+1 üretir.

### 3) İndeks stratejisi tanımlı değil

**Kanıt:**

- Model alanlarında `db_index=True` veya `Meta.indexes` neredeyse yok.
- Sık filtrelenen alanlar (tarih, durum, cari FK, fatura_no) için indeks beyanı eksik.

**Risk:**

- 50k+ kayıt sonrası listeleme/filtre sorguları yavaşlar.
- Kullanıcı "sistem ağırlaştı" şikayetiyle gelir.

### 4) Pagination kullanımı tutarsız

**Kanıt:**

- Bazı liste view'larında sayfalama yok; tüm kayıtlar tek sayfada render ediliyor.
- Tahsilat, gider, hareket listeleri büyük veride sayfayı bloklar.

### 5) Performans ölçümü yapılmıyor

**Kanıt:**

- `django-debug-toolbar` DEBUG modda var (iyi) ama:
- Üretim modunda yavaş sorgu logu yok.
- Yavaş endpoint için bir threshold uyarısı yok.

### 6) Statik dosyalar için cache yok

**Kanıt:**

- `whitenoise` mevcut ama `CompressedManifestStaticFilesStorage` aktif değil.
- Tarayıcıya gönderilen `Cache-Control` başlığı varsayılan.

## Hedef standart

- Toplulaştırma DB seviyesinde yapılmalı (`aggregate`, `annotate`).
- N+1 sorguları regresyon olarak yakalanmalı (assertNumQueries testleri).
- Sık filtrelenen alanlarda indeks beyanı olmalı.
- Tüm liste sayfalarında **pagination** veya tarih filtresi olmalı.
- Yavaş sorgular loglanmalı (>500 ms).

## Önerilen uygulama yaklaşımı

1. **Performans envanteri:** En büyük 5 view (`rapor/views.py`, `dashboard/views.py`, `stok/views.py`, `fatura/views.py`, `tahsilat/views.py`) için `silk` veya `debug-toolbar` ile sorgu sayısı + süre kaydet.
2. **Toplulaştırmayı DB'ye taşı:**
   ```python
   from django.db.models import Sum, Count
   Fatura.objects.filter(tarih__year=yil).aggregate(
       toplam=Sum("kalemler__tutar"),
       adet=Count("id"),
   )
   ```
3. **Indeks beyanları ekle:**
   ```python
   class Meta:
       indexes = [
           models.Index(fields=["tarih"]),
           models.Index(fields=["cari", "tarih"]),
           models.Index(fields=["durum"]),
       ]
   ```
4. **Pagination standardı:** Tüm liste view'larında `Paginator(qs, 50)` veya filtreli liste zorunlu.
5. **Yavaş sorgu logu:** `django.db.backends` logger'ına eşik tabanlı handler bağla.
6. **Statik dosya cache:** `STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"`.
7. **N+1 testi:**
   ```python
   with self.assertNumQueries(3):
       self.client.get("/fatura/")
   ```

## Kabul kriterleri

- Dashboard ve rapor sayfaları için DB sorgu sayısı sabittir (veri büyüklüğüne göre artmaz).
- Liste sayfalarının hiçbiri 100'den fazla kaydı tek seferde render etmez.
- Kritik view'lar için `assertNumQueries` regresyon testleri vardır.
- `>500 ms` süren sorgular `logs/uygulama.log` içinde uyarı seviyesinde görülür.
- Statik dosyalar uzun süreli cache başlıkları ile servis edilir.

## Sonraki iş paketleri

- P2.8 — Performans envanteri ve baseline ölçümü
- P2.9 — Indeks beyanları + migration
- P2.10 — Pagination standardı
- P2.11 — N+1 regresyon test suite'i
