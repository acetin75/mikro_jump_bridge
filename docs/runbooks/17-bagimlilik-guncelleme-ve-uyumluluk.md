# Runbook 17 — Bağımlılık Güncelleme ve Uyumluluk Yönetimi

**Faz:** P1  
**Durum:** ✅ Aktif (2026-05-23)

---

## Prensipler

1. **Kırılmayan güncelleme**: Yama sürümler (x.y.**Z**) → doğrudan güncelle.  
   Minor sürümler (x.**Y**.0) → CHANGELOG oku, test et, sonra güncelle.  
   Major sürümler (**X**.0.0) → ayrı branch aç, kapsamlı test, yalnızca kasıtlı geç.

2. **Sabitlenmiş sürümler**: `requirements.txt`'te tam sürüm (`==`) kullanılır —  
   `>=` veya `~=` gibi esnek pinler üretim ortamında tehlikelidir.

3. **Test et, sonra kaydet**: Güncelleme sonrası `python manage.py check` ve  
   uygulama başlatma testi zorunludur.

---

## Aylık Güncelleme Akışı

### Adım 1 — Güncel olmayan paketleri listele

```bat
.venv\Scripts\python.exe -m pip list --outdated --format=columns
```

### Adım 2 — Güvenlik açığı var mı?

```bat
.venv\Scripts\python.exe -m pip_audit -r requirements.txt
```

CVE bulunan paketler → **hemen** güncelle (bekleme yok).

### Adım 3 — Güvenli güncelleme

```bat
REM Tek paket güncelle (önerilen — kontrollü)
.venv\Scripts\python.exe -m pip install "django==X.Y.Z"

REM Sistem kontrolü
.venv\Scripts\python.exe manage.py check

REM Uygulama başlatma testi
.venv\Scripts\python.exe manage.py runserver --noreload
```

### Adım 4 — requirements.txt'i sabitle

```bat
.venv\Scripts\python.exe -m pip freeze > requirements_frozen.txt
REM Değişiklikleri manuel olarak requirements.txt'e yansıt
```

---

## Django Sürüm Takibi

| Sürüm | LTS? | Destek Bitiş |
|---|---|---|
| Django 5.2 | ✅ LTS | Nisan 2028 |
| Django 6.0 | — | Aralık 2026 |
| Django 6.1 (LTS) | Bekleniyor | — |

**Kural:** LTS olmayan sürüme geçme. LTS → LTS atla.  
Yeni LTS çıkınca → ayrı branch'te migration denemesi yap, geçince main'e al.

---

## Kütüphane Güncelleme Notları (Bilinen Kırılmalar)

### `requests` 2.x → 3.x
- Muhtemelen `Response.text` encoding davranışı değişir.
- `client.py`'daki `_post` metodunu test et.

### `whitenoise` 6.x → 7.x
- `STATICFILES_STORAGE` ayarı kaldırıldı — `WHITENOISE_KEEP_ONLY_HASHED_FILES` yeni format.

### `django-widget-tweaks` 1.5+
- API değişmez, güvenle güncellenebilir.

### `defusedxml` 0.7+
- API sabittir, güvenle güncellenebilir.

### `python-decouple` 3.8+
- `config()` fonksiyonu değişmez.

---

## Otomatik Güvenlik Bildirimi (Opsiyonel)

GitHub → Settings → Security → Dependabot alerts → Enable  
`acetin75/mikro_jump_bridge` repo'sunda aktifleştirilirse,  
`requirements.txt` taranır ve CVE bulunduğunda GitHub otomatik issue açar.
