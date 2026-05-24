# Runbook 14 — Modüler yapı ve kod boyut standartları

**Faz:** P2  
**Durum:** Tespit edildi, uygulanmadı

## Amaç

Dosyaların ve fonksiyonların **belirli bir büyüklüğü geçmemesini** kural haline getirmek.
Büyüyen `views.py` dosyaları okumayı, test etmeyi ve gözden geçirmeyi zorlaştırır; modülerlik bakım maliyetini düşürür.

> **Bağlantılı runbook'lar:** 09 (mimari/servis katmanı), 04 (test edilebilirlik).

## Mevcut durum ve kanıtlar

### 1) Bazı dosyalar tek dosya halinde büyümüş

**Ölçüm (`.py` dosyaları, migration hariç):**

| Dosya | Satır |
|---|---|
| `rapor/views.py` | 318 |
| `stok/views.py` | 236 |
| `dashboard/views.py` | 214 |
| `fatura/views.py` | 203 |
| `fatura/efatura.py` | 156 |
| `banka/parser.py` | 155 |
| `fatura/models.py` | 138 |

**Ölçüm (template dosyaları):**

| Dosya | Satır |
|---|---|
| `templates/dashboard/index.html` | 390 |
| `templates/base.html` | 206 |
| `templates/fatura/form.html` | 197 |
| `templates/stok/degerleme.html` | 177 |

**Risk:**

- 200+ satırlık `views.py` içinde 8–12 view fonksiyonu bir arada bulunuyor.
- Tek dosyada PR çakışması, code review yorgunluğu, test izolasyonu zorluğu.
- 390 satırlık `dashboard/index.html` içinde 4 ayrı kart bloğu + filtreler + tablo birlikte yaşıyor.

### 2) Boyut/karmaşıklık sınırı tanımsız

**Kanıt:**

- `pyproject.toml` `[tool.ruff.lint]` içinde **yalnızca** `E`, `F`, `W`, `I` seçili.
- `C901` (McCabe karmaşıklığı), `PLR0915` (çok satırlı fonksiyon), `PLR0912` (çok branch) gibi kurallar **kapalı**.
- `max-complexity` ayarı yok.
- Template'ler için bir "max satır" disiplini hiç yok.

### 3) Yardımcı / servis dosyalarına ayırma standardı yok

**Kanıt:**

- `kasa/utils.py` mevcut (iyi).
- `fatura/efatura.py`, `banka/parser.py`, `stok/degerleme.py` mevcut (iyi yön).
- Ama `rapor/`, `dashboard/`, `stok/` view'larında bu ayrım yapılmamış.
- "Ne zaman `utils.py` / `services.py` / `selectors.py` oluşturulur" kuralı yazılı değil.

### 4) Template kompozisyon disiplini yok

**Kanıt:**

- `templates/dashboard/index.html` parçalara (`{% include %}`) bölünmemiş.
- Aynı stat-kart bloğu farklı template'lerde kopyalanmış (`templates/kasa/detay.html`, `templates/stok/degerleme.html`).
- Ortak partial klasörü (`templates/_partials/`) yok.

## Hedef standart

### Boyut sınırları (tavsiye, ruff/pre-commit ile sert)

| Birim | Yumuşak limit (uyarı) | Sert limit (hata) |
|---|---|---|
| Python fonksiyon | 40 satır | 80 satır |
| McCabe karmaşıklığı | 8 | 12 |
| Python dosyası | 250 satır | 400 satır |
| Template dosyası | 200 satır | 350 satır |
| Tek fonksiyon parametre sayısı | 5 | 8 |

### App içi standart düzen

```
appadi/
├── models.py        # sadece model + Meta + __str__ + @property
├── forms.py
├── urls.py
├── admin.py
├── views.py         # sadece HTTP orkestrasyonu, ince katman
├── services.py      # iş kuralları, çok adımlı yazma akışları (atomic)
├── selectors.py     # okuma-yönelimli karmaşık sorgular
├── utils.py         # yan etkisiz yardımcılar
└── (views/ klasörü) # views.py 250'yi geçerse paketleştir
```

### Template kompozisyon

- 200 satırı geçen template **bölünür**.
- Tekrarlayan bloklar `templates/_partials/` altına alınır.
- Sayfa şablonu yalnızca `{% include %}` ve blok düzenlemesi yapar.

## Önerilen uygulama yaklaşımı

1. **Ruff kurallarını sıkılaştır:**
   ```toml
   [tool.ruff.lint]
   select = ["E", "F", "W", "I", "C90", "PLR0911", "PLR0912", "PLR0915"]

   [tool.ruff.lint.mccabe]
   max-complexity = 10

   [tool.ruff.lint.pylint]
   max-statements = 50
   max-args = 6
   ```
2. **Dosya satır eşiği için custom check:**
   - `scripts/check_file_size.py` → 400+ satırlı `.py`, 350+ satırlı `.html` için CI hatası.
   - Geçici istisnalar `pyproject.toml` veya allowlist dosyasında listelenir, görünür kalır.
3. **Mevcut "şişkin" dosyaları refactor planına al:**
   - `rapor/views.py` → `rapor/views.py` + `rapor/services.py` + `rapor/selectors.py`.
   - `dashboard/views.py` → kart hesaplamaları `dashboard/services.py`'ye.
   - `fatura/views.py` → finansal yan etkiler `fatura/services.py`'ye (runbook 09 ile birlikte).
4. **Template kütüphanesi başlat:**
   - `templates/_partials/stat_card.html` → `dashboard`, `kasa`, `stok` tarafından `include` edilir.
   - `templates/_partials/filtre_cubugu.html` → liste sayfaları paylaşır.
5. **Definition of Done:** Yeni eklenen kod bu limitleri **geçemez**; geçerse PR otomatik kırılır.

## Kabul kriterleri

- `ruff check` McCabe ve fonksiyon uzunluğu kurallarıyla yeşil döner (mevcut ihlaller refactor edilmiş veya `# noqa` ile geçici işaretli).
- 400+ satırlı `.py` ve 350+ satırlı `.html` CI'da kırmızıya düşer.
- `templates/_partials/` klasöründe en az 2 ortak parça vardır ve farklı template'lerde `include` edilmiştir.
- `services.py` / `selectors.py` deseni en az iki app'te uygulanmıştır (fatura, rapor).
- Yeni özelliklerde 80 satırlık fonksiyon veya 400 satırlık dosya görünmüyor.

## Sonraki iş paketleri

- P2.13 — Ruff kurallarını sıkılaştır + baseline ihlal listesi
- P2.14 — `scripts/check_file_size.py` ve CI entegrasyonu
- P2.15 — En şişkin 4 dosyayı refactor et (`rapor/`, `dashboard/`, `fatura/`, `stok/`)
- P2.16 — `templates/_partials/` ortak bileşen kitaplığı
