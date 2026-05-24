# Runbook 16 — Kod Kalitesi Araçları ve Git/Copilot Geliştirme Protokolü

**Faz:** P1  
**Durum:** ✅ Aktif (2026-05-23)

---

## Araç Seti

| Araç | Amaç | Sıklık |
|---|---|---|
| `ruff` | Linter + formatter (E/F/W/I kuralları) | Her kaydetmede (VS Code) |
| `vulture` | Ölü kod tespiti | Haftada 1 / PR öncesi |
| `pip-audit` | Bağımlılık güvenlik açığı (CVE taraması) | Commit öncesi |
| `pip list --outdated` | Kütüphane güncelleme kontrolü | Ayda 1 |
| `django check --deploy` | Django üretim güvenlik kontrolü | Deploy öncesi |

---

## Kurulum

```bat
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

---

## Toplu Çalıştırma

```bat
kontrol.bat
```

`kontrol.bat` — proje kökünde. 5 aşama çalışır, pause ile bekler.

---

## VS Code Otomatik Lint (Zaten Aktif)

`pyproject.toml` → `[tool.ruff]` ile yapılandırılmış.  
VS Code ruff extension kaydetme sırasında otomatik düzeltirir.

---

## Vulture — Ölü Kod

```bat
.venv\Scripts\python.exe -m vulture sync_motor hesap_yonetimi lisans posta kullanici mikro_sync --min-confidence 80
```

**Yanlış pozitif nasıl susturulur:**
```python
# views.py içinde kullanılmayan ama Django'nun çağırdığı fonksiyon
def get_queryset(self):  # noqa: vulture
    ...
```
Ya da `pyproject.toml` → `[tool.vulture]` → `ignore_names` listesine ekle.

---

## pip-audit — Güvenlik Taraması

```bat
.venv\Scripts\python.exe -m pip_audit -r requirements.txt
```

Çıktıda `No known vulnerabilities found` görünmeli.  
Güvenlik açığı bulunursa: `pip install paket==x.y.z` ile güvenli sürüme geç,  
`requirements.txt`'i güncelle, test et, commit et.

---

## Git + Copilot Geliştirme Akışı

### Standart commit döngüsü

```bat
REM 1. Değişiklikleri kontrol et
git status
git diff

REM 2. Kalite kontrolü (opsiyonel ama önerilir)
kontrol.bat

REM 3. Stage et
git add -p          ← satır satır gözden geçirerek (önerilen)
REM veya
git add .

REM 4. Commit — Türkçe, kısa açıklama
git commit -m "hesap_yonetimi: firma kartları ve bakiye raporu eklendi"

REM 5. Push
git push
```

### Commit mesajı formatı

```
<app/konu>: <ne yapıldı> (<neden — opsiyonel>)
```

Örnekler:
- `sync_motor: sql_oku() metodu eklendi`
- `hesap_yonetimi: cari detay şablonu oluşturuldu`
- `güvenlik: SECRET_KEY fail-fast koruması eklendi`
- `ruff: F401 hataları giderildi`

### Copilot ile çalışırken

- Copilot her büyük değişiklikten sonra `django check` çalıştırır — hata yoksa commit et.
- Copilot `manage.py migrate` çalıştırmaz — `migrate` senin sorumluluğundadır.
- Model değişikliğinde: Copilot `makemigrations` komutunu söyler, sen çalıştırırsın.

---

## Duplicate Kod Tespiti

`ruff` `F811` (redefined unused) ve `E741` kurallarını otomatik yakalar.  
Manuel duplicate analizi için:

```bat
.venv\Scripts\python.exe -m ruff check . --select=F,E
```

Büyük duplicate bloklar için helper function ya da mixin oluştur —  
ama sadece 3+ kez tekrar ediyorsa (YAGNI kuralı).
