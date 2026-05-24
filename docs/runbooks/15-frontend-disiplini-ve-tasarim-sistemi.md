# Runbook 15 — Frontend disiplini ve tasarım sistemi (design tokens)

**Faz:** P2  
**Durum:** Tespit edildi, uygulanmadı

## Amaç

Arayüzde **renk, boşluk, tipografi** gibi tasarım kararlarının **tek bir kaynaktan** beslenmesini sağlamak.
Hard-coded renk/inline stil dağılımını ortadan kaldırarak tema desteği, erişilebilirlik kontrastı ve marka tutarlılığı için temel kurmak.

> **Bağlantılı runbook'lar:** 14 (modülerlik / template parçalama), 09 (mimari).

## Mevcut durum ve kanıtlar

### 1) Inline hardcoded renkler template'lere yayılmış

**Kanıt — `grep` ile bulunan inline hex renkler:**

- `templates/dashboard/index.html:106` → `style="background:linear-gradient(135deg,#3b82f6,#6366f1)"`
- `templates/dashboard/index.html:117` → `#10b981,#059669`
- `templates/dashboard/index.html:128` → `#f59e0b,#d97706`
- `templates/dashboard/index.html:139` → `#ef4444,#dc2626`
- `templates/kasa/detay.html:22,33,44,55` → 4 farklı gradient inline
- `templates/stok/degerleme.html:20,31,42` → 3 gradient inline
- `templates/fatura/print.html:158` → `border:1px solid #ddd;color:#444`

**Risk:**

- Marka rengi değişirse **8+ dosyada** elle düzenleme gerekir.
- Açık/koyu tema desteği imkânsız.
- Aynı "başarı yeşili" için iki farklı tonlama mevcut (`#10b981/#059669` vs `#047857/#10b981`) — tutarsız.
- Erişilebilirlik (WCAG kontrast oranı) hiç ölçülemiyor.

### 2) Tasarım token kaynağı yok

**Kanıt:**

- `static/` altında `tokens.css` / `theme.css` / `variables.css` yok.
- `templates/base.html` Bootstrap CDN'i çekiyor ama `:root { --primary: ... }` özel değişken seti tanımlı değil.
- Bootstrap'in mevcut CSS değişkenleri (`--bs-primary` vb.) kullanılmıyor.

### 3) Stil dağılımı: inline + CDN + (yer yer) sınıf

**Kanıt:**

- Inline `style="..."` (yukarıdaki örnekler).
- Bootstrap utility class'ları (`text-success`, `badge bg-warning`) — iyi yön.
- Özel CSS dosyası ya yok ya da çok sınırlı.
- Aynı görsel (stat-card) farklı template'lerde kopyalanmış — ortak CSS sınıfı yerine inline stil tekrarı.

### 4) İkon ve emoji kullanımı belirsiz

**Kanıt:**

- `copilot-instructions.md` Bootstrap Icons kullanılır diyor (iyi).
- Bazı template'lerde emoji (`📊`, `✅`) kullanılmış olabilir (`grep` taranmalı).
- Erişilebilir alternatif metin (`aria-label`, `sr-only`) disiplini yazılı değil.

### 5) Erişilebilirlik (a11y) standardı yok

**Kanıt:**

- `templates/base.html` `lang="tr"` içeriyor (iyi).
- Form etiket-input bağlantısı `BootstrapFormMixin` sayesinde büyük ölçüde sağlanıyor (iyi).
- Ama `aria-*`, kontrast denetimi, klavye navigasyonu, odak halkası testi yok.

### 6) Dark mode / yazdırma stilleri ayrı yönetilmiyor

**Kanıt:**

- `templates/fatura/print.html` ayrı template — iyi.
- Ama yazdırma için `@media print` global kuralları, marj/font ayarları tek bir CSS'te toplanmış değil.

## Hedef standart

- Tüm renk, boşluk, font değişiklikleri **bir tek CSS değişken seti** (design tokens) üzerinden yapılır.
- Template'lerde **inline hex renk yasak** — sadece sınıf veya `var(--token)` kullanılır.
- Tekrarlayan görsel bileşenler (stat-card, badge, filtre kutusu) **ortak CSS sınıfı**na sahiptir.
- Tüm interaktif elemanlar `aria-*` etiketleri ve klavye desteğine sahiptir.
- Açık/koyu tema değişimi tek bir attribute (`data-theme="dark"`) ile mümkündür.

## Önerilen uygulama yaklaşımı

1. **Token dosyası oluştur:** `static/css/tokens.css`
   ```css
   :root {
     /* Renk paleti */
     --renk-primary:    #3b82f6;
     --renk-primary-2:  #6366f1;
     --renk-success:    #10b981;
     --renk-success-2:  #059669;
     --renk-warning:    #f59e0b;
     --renk-warning-2:  #d97706;
     --renk-danger:     #ef4444;
     --renk-danger-2:   #dc2626;
     --renk-info:       #1e40af;
     --renk-muted:      #64748b;

     /* Yarıçap, gölge, boşluk */
     --radius-md: 0.5rem;
     --gap-card: 1rem;

     /* Tipografi */
     --font-sans: system-ui, "Segoe UI", sans-serif;
   }

   [data-theme="dark"] {
     /* ileride doldurulacak */
   }
   ```
2. **Ortak bileşen CSS'i:** `static/css/components.css`
   ```css
   .stat-card { border-radius: var(--radius-md); padding: 1.25rem; color: #fff; }
   .stat-card--primary { background: linear-gradient(135deg, var(--renk-primary), var(--renk-primary-2)); }
   .stat-card--success { background: linear-gradient(135deg, var(--renk-success), var(--renk-success-2)); }
   .stat-card--warning { background: linear-gradient(135deg, var(--renk-warning), var(--renk-warning-2)); }
   .stat-card--danger  { background: linear-gradient(135deg, var(--renk-danger),  var(--renk-danger-2)); }
   ```
3. **Template'leri taşı:**
   ```html
   <!-- ÖNCE -->
   <div class="stat-card" style="background:linear-gradient(135deg,#3b82f6,#6366f1)">

   <!-- SONRA -->
   <div class="stat-card stat-card--primary">
   ```
4. **Ortak partial ekle:** `templates/_partials/stat_card.html` — runbook 14 ile birleşik.
5. **Hardcoded renk yasağı CI kuralı:**
   ```bash
   # scripts/check_no_inline_color.py
   # templates/ altında style="..." içinde #hex veya rgb() arar.
   ```
   CI'da bulursa PR kırılır.
6. **Erişilebilirlik denetimi:**
   - Form input'lar için `aria-describedby` (yardım metni varsa).
   - Renkle ifade edilen durumların yanına metin/ikon ekle (renk körü kullanıcı için).
   - Kontrast oranı WCAG AA (4.5:1) hedefi — token seti bu eşiğe göre seçilmelidir.
7. **Yazdırma stili:** `static/css/print.css` ayrı dosyada, `@media print` blokları toplanmış.

## Kabul kriterleri

- `grep -r 'style=.*#[0-9a-fA-F]\{3,6\}' templates/` boş sonuç döner (zorunlu istisnalar `# allow` listesinde).
- Tüm gradient kart blokları `.stat-card--{varyant}` sınıfı ile çalışır.
- Marka rengini değiştirmek için **yalnızca `tokens.css`** düzenlenir.
- `templates/_partials/stat_card.html` en az 3 farklı sayfada `{% include %}` edilir.
- Kontrast denetimi (manuel veya `axe`) ana sayfalarda hata vermez.

## Sonraki iş paketleri

- P2.17 — `tokens.css` + `components.css` çıkar
- P2.18 — Inline renkleri taşı (dashboard, kasa, stok, fatura print)
- P2.19 — `templates/_partials/` ortak bileşenler (runbook 14 ile birlikte)
- P2.20 — Hardcoded renk yasağı CI kuralı
- P2.21 — Erişilebilirlik denetim listesi + manuel test prosedürü
