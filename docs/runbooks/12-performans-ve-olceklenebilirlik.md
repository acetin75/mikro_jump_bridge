# Runbook 12 — Performans ve ölçeklenebilirlik

**Faz:** P2
**Durum:** ⛔ Açık — önbellek yok, toplu veri koruması yok

## Amaç

Mikro ERP API gecikmelerinin kullanıcıya yansımasını azaltmak; büyük import ve sorgularda timeout ve bellek sorunlarını önlemek.

---

## Mevcut durum ve kanıtlar

### 1) Her sayfa yüklemesi Mikro ERP'ye canlı sorgu yapıyor

**Kanıt:** `hesap_yonetimi/views.py` — her view çağrısında `MikroApiClient.sql_oku()` → `requests.post()` → Mikro ERP API.

- `panel()` — bakiye özeti sorgusu
- `firma_kartlari()` — tüm cari listesi sorgusu
- `bakiye_raporu()` — tüm açık bakiyeler

Mikro ERP sunucusu yavaş/meşgul olduğunda her sayfa yüklemesi kullanıcıyı bekletir.

### 2) Toplu import için chunk kontrolü yok

**Kanıt:** `sync_motor/views.py` → `import_baslat()` — Mikro API'den çekilen tüm faturalar tek seferde işleniyor.

Geniş tarih aralıklı import (ör. 6 aylık) beklenen sonuç: binlerce fatura, uzun işlem süresi, timeout.

### 3) `bakiye_raporu` / `firma_kartlari` pagination yok

**Kanıt:** `hesap_yonetimi/views.py` → sorgu sonucu doğrudan template'e `{"kayitlar": veri}` ile geçiliyor, `Paginator` kullanılmıyor.

Büyük firmalarda yüzlerce cari kartı veya binlerce bakiye satırı tek sayfada render ediliyor.

---

## Hedef standart

| Sorun | Çözüm | Öncelik |
|---|---|---|
| Tekrarlı Mikro ERP sorguları | Django cache (60 sn) | P1 |
| Büyük import → timeout | Chunk işleme (100'lük paketler) | P1 |
| Sayfalanmamış listeler | `Paginator` (sayfa başı 50) | P2 |
| Panel bakiye çağrısı | `request.session` kısa önbellek | P2 |

---

## Önerilen uygulama yaklaşımı

### 1. `hesap_yonetimi` sorgularına basit cache

```python
from django.core.cache import cache

def firma_kartlari(request):
    firma = _aktif_firma(request)
    cache_key = f"cari_liste_{firma.pk}"
    veri = cache.get(cache_key)
    if veri is None:
        client = MikroApiClient(firma)
        veri = client.sql_oku(CARI_LISTESI_SQL)
        cache.set(cache_key, veri, timeout=60)  # 60 saniye
    ...
```

Django'nun varsayılan LocMemCache (settings'e ekstra kurulum gerekmez).

### 2. Import chunk işleme

```python
# sync_motor/views.py
CHUNK_BOYUT = 100

def import_baslat(request, pk):
    ...
    faturalar = client.gelen_faturalar(baslangic, bitis)
    for i in range(0, len(faturalar), CHUNK_BOYUT):
        chunk = faturalar[i:i + CHUNK_BOYUT]
        with transaction.atomic():
            MikroFatura.objects.bulk_create(
                [_fatura_nesne_olustur(f, firma) for f in chunk],
                ignore_conflicts=True
            )
```

### 3. Sayfalama

```python
from django.core.paginator import Paginator

paginator = Paginator(veri, 50)
sayfa = request.GET.get("sayfa", 1)
kayitlar = paginator.get_page(sayfa)
```

### 4. `settings.py` — önbellek ayarı

```python
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "mikro-sync-cache",
    }
}
```

---

## Kabul kriterleri

- `firma_kartlari` aynı firma için 60 saniyede tekrar yüklenirse Mikro ERP'ye istek gitmiyor
- 1000+ fatura import edildiğinde timeout oluşmuyor
- `bakiye_raporu` 500+ satırda sayfa başı 50 gösteriyor
- Cache sonrası `kontrol.bat` + django check temiz

---

## Sonraki iş paketleri

- P1.1 — `settings.py` LocMemCache tanımı
- P1.2 — `firma_kartlari()` ve `panel()` cache
- P1.3 — import chunk işleme
- P2.1 — `bakiye_raporu` Paginator
- P2.2 — cache invalidation (firma ayarı değişince)
