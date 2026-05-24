# Runbook 15 — Frontend disiplini ve tasarım sistemi

**Faz:** P2
**Durum:** ⛔ Açık — inline JS/CSS var, CDN yönetimi dağınık

## Amaç

Template'lerdeki inline JavaScript ve CSS'i statik dosyalara taşımak; CDN bağımlılıklarını merkezi olarak yönetmek; Bootstrap 5.3 kullanımını tutarlı hale getirmek.

---

## Mevcut durum ve kanıtlar

### 1) Büyük inline JavaScript blokları

**Kanıt:**

- `templates/hesap_yonetimi/hesap_hareketleri.html` (385 satır):
  - `toggleGrupla()`, `buildGruplama()`, toplam hesaplama fonksiyonları — template içinde `<script>` bloğu
  - Select2 başlatma: `$(document).ready(function() { ... })`
  - `formatPara()` yardımcı fonksiyonu — template içi tanımlı

- `templates/hesap_yonetimi/firma_sec.html` (330 satır):
  - Arama/filtreleme JS template içinde

### 2) CDN bağımlılıkları tek tek template'lerde

**Kanıt:** `templates/hesap_yonetimi/hesap_hareketleri.html` içinde:

```html
<!-- SADECE bu template'de, başka hiçbir yerde değil -->
<link href="https://cdn.jsdelivr.net/npm/select2@4.1.0/dist/css/select2.min.css" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/select2@4.1.0/dist/js/select2.full.min.js"></script>
```

`base.html` CDN listesinde Select2 yok. Tutarsız CDN yönetimi.

### 3) Hardcoded renkler ve stiller

**Kanıt:** Template'lerde `style="color: red"`, `style="background: #f8f9fa"` gibi satır içi stiller.

### 4) jQuery bağımlılığı (Select2 için)

**Kanıt:** Select2, jQuery gerektiriyor. jQuery `base.html`'de mi var kontrol edilmeli.  
Bootstrap 5.x jQuery bağımlılığını kaldırdı — Select2 için jQuery eklemek gerekebilir.

---

## Hedef standart

### Dosya organizasyonu

```
static/
├── css/
│   └── mikro.css          ← projeye özgü CSS (Bootstrap override'lar)
└── js/
    ├── hesap_hareketleri.js  ← gruplama + toplam JS
    ├── firma_sec.js          ← cari seçim filtresi
    └── utils.js              ← formatPara() gibi paylaşılan yardımcılar
```

### CDN yönetim kuralı

Tüm CDN linkleri **yalnızca** `base.html` içinde olur.  
Template bazlı CDN yasaktır.  
Sayfa bazlı JS → `{% block extra_js %}` block ile yüklenir.

### Bootstrap 5.3 kullanım kılavuzu

| Amaç | Kullan | Kullanma |
|---|---|---|
| Renkler | `text-danger`, `bg-warning` | `style="color:red"` |
| Aralıklar | `mt-3`, `p-2` | `style="margin-top:12px"` |
| Tablolar | `table-striped table-hover` | özel CSS |
| Butonlar | `btn btn-primary` | hardcoded renk |
| Uyarı kutuları | `alert alert-warning` | custom div |

---

## Önerilen uygulama yaklaşımı

### 1. `hesap_hareketleri.js` oluştur

```javascript
// static/js/hesap_hareketleri.js
function formatPara(sayi) {
    return new Intl.NumberFormat("tr-TR", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(sayi);
}

function toggleGrupla() { ... }
function buildGruplama(veri) { ... }

document.addEventListener("DOMContentLoaded", function () {
    // Select2 başlatma buraya
});
```

### 2. `base.html` içinde Select2 CDN

Select2 birden fazla sayfada kullanılacaksa `base.html`'e taşı:

```html
<!-- base.html -->
<link href="https://cdn.jsdelivr.net/npm/select2@4.1.0/dist/css/select2.min.css" rel="stylesheet">
...
<script src="https://cdn.jsdelivr.net/npm/select2@4.1.0/dist/js/select2.full.min.js"></script>
```

Tek sayfada kalacaksa `{% block extra_css %}` / `{% block extra_js %}` ile yükle.

### 3. Inline stil tarama

```bat
grep -rn "style=" templates/ | grep -v "display:none" | grep -v "base.html"
```

Çıktıdaki `style=` satırlarını Bootstrap utility class'larıyla değiştir.

---

## Kabul kriterleri

- `hesap_hareketleri.html` içinde `<script>` bloğu kalmıyor
- CDN bağımlılıkları `base.html` veya `{% block extra_js %}` üzerinden yönetiliyor
- `templates/` içinde `style="color:` veya `style="background:` kalmıyor
- `static/js/` altında en az bir modüler JS dosyası oluşturulmuş

---

## Sonraki iş paketleri

- P2.1 — `static/js/hesap_hareketleri.js` taşıma
- P2.2 — `static/js/utils.js` (formatPara ve paylaşılan fonksiyonlar)
- P2.3 — Inline stil temizliği (grep ile tespit, utility class ile replace)
- P2.4 — Select2 CDN → `base.html` konsolidasyonu
