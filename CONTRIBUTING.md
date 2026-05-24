# Katkıda Bulunma Rehberi

Mikro Jump Bridge'e katkıda bulunduğunuz için teşekkürler. Bu doküman kısa ve uygulamaya yönelik bir başlangıç rehberidir.

> **Detaylı standartlar:** [docs/runbooks/](docs/runbooks/) klasöründe 18 konuda runbook bulunur. Yeni özellik veya yapısal değişiklik yapmadan önce ilgili runbook'u okuyun.

---

## Geliştirme Ortamı

1. Repository'yi klonlayın:
   ```bat
   git clone https://github.com/acetin75/mikro_jump_bridge.git
   cd mikro_jump_bridge
   ```
2. `baslat.bat` çalıştırın — sanal ortam, paketler ve migrate otomatik yapılır.
3. Geliştirme araçlarını kurun:
   ```bat
   .venv\Scripts\python.exe -m pip install -r requirements-dev.txt
   ```

---

## Çalışma Akışı

1. **Branch açın** — `master` üzerinde doğrudan çalışmayın:
   ```bat
   git checkout -b ozellik/kisa-aciklama
   ```
2. **Değişiklikleri yapın** — kod standartları için [docs/runbooks/14-modulerlik-ve-kod-boyut-standartlari.md](docs/runbooks/14-modulerlik-ve-kod-boyut-standartlari.md) ve [docs/runbooks/16-kod-kalitesi-araclar-ve-git-protokolu.md](docs/runbooks/16-kod-kalitesi-araclar-ve-git-protokolu.md) dosyalarına bakın.
3. **Kalite kontrolünü çalıştırın**:
   ```bat
   kontrol.bat
   ```
   Beş aşama temiz olmalı: ruff → vulture → pip-audit → pip outdated → django check.
4. **Migration gerekiyorsa** model değişikliği sonrası:
   ```bat
   .venv\Scripts\python.exe manage.py makemigrations
   .venv\Scripts\python.exe manage.py migrate
   ```
5. **Commit edin** — Türkçe, kısa açıklama:
   ```bat
   git add -p
   git commit -m "app/konu: ne yapıldı"
   ```
6. **Push + Pull Request**:
   ```bat
   git push -u origin ozellik/kisa-aciklama
   ```

---

## Commit Mesajı Formatı

```
<app/konu>: <ne yapıldı> (<neden — opsiyonel>)
```

Örnekler:
- `hesap_yonetimi: bakiye raporu eklendi`
- `sync_motor: sql_oku() metodu eklendi`
- `güvenlik: SECRET_KEY fail-fast koruması eklendi`
- `ruff: F401 hataları giderildi`

> İngilizce conventional commit (`feat:`, `fix:`, `chore:`) **kullanılmaz** — projede Türkçe `app/konu:` formatı standarttır.

---

## Pull Request Beklentileri

- `kontrol.bat` temiz çıkıyor (5 aşama da yeşil).
- Yeni Python dosyaları soft limit 200 / hard limit 300 satır içinde.
- Para alanları `DecimalField(max_digits=14, decimal_places=2)`.
- Logger: `logger = logging.getLogger("mikro_sync")` — `print()` kullanılmaz.
- Hassas veri (VKN, e-posta, telefon, şifre) log'a yazılmaz.
- Function-based views tercih edilir; `@login_required` zorunlu.
- URL adları `app_name` namespace **olmadan** kullanılır.
- Türkçe verbose_name + verbose_name_plural model `Meta`'sında tanımlı.

---

## Hata Bildirme

GitHub Issues üzerinden bildirin. Lütfen şunları ekleyin:
- Hatanın ekran görüntüsü veya log çıktısı (`logs/mikro_sync.log`)
- Adım adım nasıl tekrarlanacağı
- Beklenen ve gerçekleşen davranış
- Python sürümü + işletim sistemi

> **Güvenlik açıkları**: Issue açmayın. Bunun yerine doğrudan e-posta ile bildirin.

---

## Lisans

Katkılarınız [MIT Lisansı](LICENSE) altında dahil edilir.
