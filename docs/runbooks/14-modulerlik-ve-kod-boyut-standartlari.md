# Runbook 14 — Modülerlik ve kod boyut standartları

**Faz:** P2
**Durum:** ⛔ Açık — limit aşımı var

## Amaç

Tek dosyaların aşırı büyümesini önlemek; yeni özellik eklemenin mevcut büyük dosyaları daha da büyütmemesini sağlamak.

---

## Mevcut durum ve kanıtlar

### 1) Dosya boyut ölçümü (Mayıs 2026)

| Dosya | Satır | Durum |
|---|---|---|
| `hesap_yonetimi/views.py` | **503** | 🔴 Sınır aşıldı (max 300) |
| `templates/hesap_yonetimi/hesap_hareketleri.html` | **385** | 🔴 Sınır aşıldı (max 300) |
| `templates/hesap_yonetimi/firma_sec.html` | **330** | 🔴 Sınır aşıldı (max 300) |
| `sync_motor/client.py` | 217 | 🟡 Yaklaşıyor (soft limit 200) |
| `sync_motor/models.py` | 111 | ✅ Uygun |
| `lisans/utils.py` | 58 | ✅ Uygun |

### 2) `hesap_yonetimi/views.py` büyüme sebebi

**Kanıt:** Tek dosyada hem view hem SQL sorguları hem veri normalizasyon hem de yardımcı fonksiyonlar var.

Çözüm: RB-09 ile paralel — servis katmanı çıkarılınca views.py küçülür.

### 3) `hesap_hareketleri.html` büyüme sebebi

**Kanıt:**
- `templates/hesap_yonetimi/hesap_hareketleri.html` (385 satır)
  - Satır 200-280 arası: gruplama mantığı için inline JavaScript
  - Satır 290-340 arası: tablo render ve toplam hesaplama JS
  - Gömülü `<style>` blokları

---

## Dosya boyut standartları

| Dosya tipi | Soft limit | Hard limit |
|---|---|---|
| Python view dosyası | 200 satır | 300 satır |
| Python model dosyası | 150 satır | 250 satır |
| Python client/utils | 200 satır | 300 satır |
| HTML template | 200 satır | 300 satır |
| JavaScript dosyası | 150 satır | 250 satır |

Soft limit aşılırsa → bölünme planı yapılır.  
Hard limit aşılırsa → yeni özellik eklenmez, önce bölünür.

---

## Önerilen uygulama yaklaşımı

### 1. `hesap_yonetimi/views.py` bölme (RB-09 ile koordineli)

```
hesap_yonetimi/
├── views.py              ← sadece HTTP katmanı (~150 satır)
├── services.py           ← SQL ve veri işleme (~200 satır)
└── utils.py              ← _aktif_firma, _firma_listesi (~30 satır)
```

### 2. `hesap_hareketleri.html` JavaScript çıkarma

```
static/js/
└── hesap_hareketleri.js  ← gruplama, toplam hesaplama JS
```

Template'de:
```html
{% block extra_js %}
<script src="{% static 'js/hesap_hareketleri.js' %}"></script>
{% endblock %}
```

### 3. `sync_motor/client.py` izleme

217 satır — şu an uygun. Her yeni metot eklenmeden önce boyut kontrol edilmeli.  
`sql_oku()` + `gelen_faturalar()` + `saglik_kontrol()` → bunlar `client.py`'da kalabilir.  
İleride: SQL sonuç → dict normalizasyon mantığı `sync_motor/mapper.py`'a taşınabilir.

---

## Kabul kriterleri

- `hesap_yonetimi/views.py` 300 satırın altına iner
- `hesap_hareketleri.html` 300 satırın altına iner
- Inline `<script>` blokları `static/js/` altındaki dosyalara taşınmış
- Vulture + ruff taşıma sonrası temiz

---

## Sonraki iş paketleri

- P2.1 — `hesap_hareketleri.js` statik dosyası oluştur
- P2.2 — `hesap_yonetimi/utils.py` (yardımcı fonksiyonlar)
- P2.3 — Boyut aşımı için `kontrol.bat`'a satır sayımı ekle (opsiyonel)
