# Runbook 04 — Test stratejisi ve kalite kapıları

**Faz:** P1
**Durum:** ⛔ Açık — iskelet dosyalar var, gerçek test yok

## Amaç

Regresyonları önlemek için kritik iş mantığı ve entegrasyon noktalarını test kapsamına almak.

---

## Mevcut durum ve kanıtlar

### 1) Test coverage neredeyse sıfır

| Dosya | Satır | Durum |
|---|---|---|
| `sync_motor/tests.py` | 95 | İskelet / placeholder |
| `hesap_yonetimi/tests.py` | 2 | Tamamen boş |
| `lisans/tests.py` | — | Dosya yok |

### 2) Test edilmesi en kritik ama test edilmeyen modüller

- `lisans/utils.py` (58 satır): `lisans_anahtari_uret()` ve `lisans_anahtari_dogrula()` — saf fonksiyonlar, test yazmak kolay.
- `lisans/models.py`: `kalan_gun`, `gecerli_mi` property'leri tarih bağımlı.
- `sync_motor/client.py` (217 satır): `MikroApiClient` — Mikro ERP'ye canlı HTTP isteği yapıyor.
- `hesap_yonetimi/views.py` (503 satır): SQL query sonuçlarını işleyen 5 büyük view.

### 3) Mikro ERP bağımlılığı mock'lanmıyor

**Kanıt:** `sync_motor/client.py` → `requests.post()` çağrısı doğrudan yapılıyor, `unittest.mock.patch` ile izole edilmemiş.

---

## Hedef standart

### Öncelikli test hedefleri (coverage > 80%)

| Modül | Test tipi | Öncelik |
|---|---|---|
| `lisans/utils.py` | Birim — saf fonksiyon | P0 |
| `lisans/models.py` | Birim — property'ler | P0 |
| `lisans/middleware.py` | Entegrasyon — redirect testi | P1 |
| `sync_motor/client.py` | Birim — mock HTTP | P1 |
| `hesap_yonetimi/views.py` | Entegrasyon — mock SQL | P2 |

---

## Önerilen uygulama yaklaşımı

### lisans/utils.py — başlangıç noktası (en kolay)

```python
# lisans/tests.py
from django.test import TestCase
from datetime import date, timedelta
from lisans.utils import lisans_anahtari_uret, lisans_anahtari_dogrula

class LisansAnahtariTest(TestCase):
    def test_gecerli_anahtar(self):
        bitis = date.today() + timedelta(days=365)
        anahtar = lisans_anahtari_uret("TEST001", bitis, "standart")
        sonuc = lisans_anahtari_dogrula(anahtar)
        self.assertIsNotNone(sonuc)
        self.assertEqual(sonuc["musteri_kodu"], "TEST001")
        self.assertEqual(sonuc["tip"], "standart")

    def test_suresi_dolmus_anahtar(self):
        bitis = date.today() - timedelta(days=1)
        anahtar = lisans_anahtari_uret("TEST001", bitis, "standart")
        self.assertIsNone(lisans_anahtari_dogrula(anahtar))

    def test_bozuk_anahtar(self):
        self.assertIsNone(lisans_anahtari_dogrula("bozuk_anahtar_degeri"))
```

### sync_motor/client.py — mock HTTP

```python
from unittest.mock import patch, MagicMock
from sync_motor.client import MikroApiClient

class MikroClientTest(TestCase):
    @patch("sync_motor.client.requests.post")
    def test_saglik_kontrol_basarili(self, mock_post):
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"Result": "OK"}
        )
        # firma_ayar fixture ile test...
```

### Kalite kapısı

`kontrol.bat` içine ekle:

```bat
.venv\Scripts\python.exe -m pytest --tb=short -q
```

---

## Kabul kriterleri

- `lisans/utils.py` → %100 branch coverage
- `lisans/models.py` → `kalan_gun`, `gecerli_mi`, `gecerlilik_durumu` her dal test edildi
- `sync_motor/client.py` → gerçek HTTP isteği olmadan test geçiyor
- `kontrol.bat` çalıştığında testler de koşuluyor

---

## Sonraki iş paketleri

- P1.1 — `lisans/tests.py` yaz (utils + models)
- P1.2 — `sync_motor/tests.py` MikroApiClient mock testi
- P1.3 — `kontrol.bat` içine pytest adımı ekle
- P2.1 — `hesap_yonetimi/views.py` entegrasyon testleri
