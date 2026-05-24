# Runbook 09 — Mimari: servis katmanı ve domain kuralları

**Faz:** P2
**Durum:** ⛔ Açık — iş mantığı view içinde, servis katmanı yok

## Amaç

`hesap_yonetimi/views.py` gibi büyük view dosyalarındaki SQL ve iş mantığını view'dan ayırmak; tekrar kullanılabilir, test edilebilir bir servis katmanı oluşturmak.

---

## Mevcut durum ve kanıtlar

### 1) 503 satırlık view dosyası

**Kanıt:** `hesap_yonetimi/views.py` — 503 satır.

Tüm bunlar tek dosyada:
- `panel()` — bakiye özeti + bağlantı durumu
- `firma_kartlari()` — cari listesi + arama filtresi
- `cari_detay()` — detay + hareketler
- `hesap_hareketleri()` — tarih aralığı + gruplama mantığı
- `bakiye_raporu()` — borç/alacak filtre + sıralama
- `odeme_planlama()` — vade hesaplama
- `_aktif_firma()`, `_firma_listesi()` — yardımcı fonksiyonlar

### 2) SQL sorguları view içinde satır içi yazılmış

**Kanıt:** `hesap_yonetimi/views.py` içinde `sql_oku()` çağrısı view fonksiyonlarının gövdesinde:

```python
# view içinde doğrudan SQL
veri = client.sql_oku("""
    SELECT ... FROM CARI_HESAPLAR
    WHERE cari_baglanti_tipi = 0
    AND cari_kod LIKE %s
""")
```

Bu sorgular test edilemiyor — view test etmek için Mikro ERP'ye canlı bağlantı gerekiyor.

### 3) `sync_motor/views.py` benzer sorun

**Kanıt:** `sync_motor/views.py` (136 satır) içinde `MikroApiClient` doğrudan çağrılıyor, bağlantı testi + import mantığı view seviyesinde.

---

## Hedef standart

```
hesap_yonetimi/
├── views.py          ← yalnızca HTTP in/out (50-80 satır/view)
├── services.py       ← iş mantığı (SQL sorguları, veri dönüşümü)
└── queries.py        ← ham SQL şablonları (sabit metin, format giriş yok)
```

### Katman sorumlulukları

| Katman | Sorumluluk | Ne içermez |
|---|---|---|
| `views.py` | HTTP al → service çağır → template'e ver | SQL, hesaplama, filtreleme |
| `services.py` | `client.sql_oku()` çağır, sonucu normalize et | HTTP request/response |
| `queries.py` | SQL metin sabitleri | Parametre birleştirme (injection riski) |

---

## Önerilen uygulama yaklaşımı

### 1. `hesap_yonetimi/services.py` oluştur

```python
# hesap_yonetimi/services.py
import logging
from sync_motor.client import MikroApiClient

logger = logging.getLogger("mikro_sync")

def cari_listesi_getir(firma_ayar, arama="", tip=""):
    """Mikro ERP'den cari kartları çeker, filtreler."""
    client = MikroApiClient(firma_ayar)
    sorgu = _CARI_LISTESI_SQL
    # parametreleri güvenli biçimde ilet...
    return client.sql_oku(sorgu)

_CARI_LISTESI_SQL = """
    SELECT cari_kod, cari_unvan1, cari_baglanti_tipi
    FROM CARI_HESAPLAR
    WHERE cari_baglanti_tipi = 0
"""
```

### 2. `views.py` ince tutulur

```python
# ÖNCE: 80 satır SQL + işleme
def firma_kartlari(request):
    firma = _aktif_firma(request)
    client = MikroApiClient(firma)
    veri = client.sql_oku("SELECT ... uzun sorgu ...")
    # 30 satır veri işleme...
    return render(request, "...", {"veri": veri})

# SONRA: 15 satır
def firma_kartlari(request):
    firma = _aktif_firma(request)
    arama = request.GET.get("q", "")
    veri = cari_listesi_getir(firma, arama=arama)
    return render(request, "...", {"veri": veri})
```

### 3. Refactor öncelik sırası

1. `hesap_hareketleri()` — en büyük, en karmaşık
2. `bakiye_raporu()` — bağımsız, izole edilebilir
3. `firma_kartlari()` + `panel()` — ortak bakiye sorgusu

---

## Kabul kriterleri

- `hesap_yonetimi/views.py` 250 satırın altına iner
- `hesap_yonetimi/services.py` oluşturulur, SQL orada
- Servis fonksiyonları mock ile test edilebilir (views.py test gerektirmez)
- `kontrol.bat` sonrası ruff + vulture temiz

---

## Sonraki iş paketleri

- P2.1 — `hesap_yonetimi/services.py` iskeleti + `hesap_hareketleri` taşıması
- P2.2 — `bakiye_raporu` servis katmanına taşıma
- P2.3 — `sync_motor/services.py` (import pipeline için)
