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

### 2) Geniş aralık SQL sorguları korumasız

**Kanıt:** `hesap_yonetimi/views.py` → `hesap_hareketleri()`, `bakiye_raporu()` — kullanıcı geniş bir tarih aralığı seçerse Mikro ERP'den binlerce satır tek seferde çekilir.

Geniş tarih aralıklı sorgu (ör. 1 yıllık) beklenen sonuç: binlerce hareket, uzun bekleme, timeout.

> İleride yazma/import akışı eklenirse bu maddeye chunk işleme standardı eklenecektir.

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

### 2. Geniş tarih aralığı uyarısı

`hesap_hareketleri` ve `bakiye_raporu` view'larında kullanıcı çok geniş tarih aralığı seçerse uyarı göster veya sorguyu reddet:

```python
MAKS_GUN = 366
if (bitis - baslangic).days > MAKS_GUN:
    messages.warning(request, f"En fazla {MAKS_GUN} günlük aralık sorgulanabilir.")
    return redirect(...)
```

> İleride yazma/import akışı eklenirse burada `CHUNK_BOYUT` ile `bulk_create(ignore_conflicts=True)` örneği yer alacaktır.

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
