# Runbook 11 — KVKK ve kişisel veri saklama

**Faz:** P1
**Durum:** ⛔ Açık — kişisel veri saklanıyor, politika yok

## Amaç

`mikro_gelen` staging alanında biriken kişisel/ticari verilerin saklama süresini belirlemek, `ham_json` içindeki gizli veri alanlarını kontrol altına almak ve olası KVKK yükümlülüklerini minimize etmek.

---

## Mevcut durum ve kanıtlar

### 1) `MikroFatura` kişisel veri alanları

**Kanıt:** `mikro_gelen/models.py` satır 36-37:

```python
fat_cari_unvan = models.CharField("Cari Ünvanı", max_length=300, blank=True)
fat_cari_vkn   = models.CharField("Vergi No", max_length=20, blank=True)
```

Ek risk: `ham_json` (satır 49) — Mikro ERP'den gelen ham veri, içinde e-posta, cep telefonu, adres gibi alanlar olabilir:

```python
ham_json = models.TextField("Ham JSON", blank=True)
```

### 2) Veri saklama süresi tanımsız

**Kanıt:** `MikroFatura.objects` üzerinde zamanlanmış temizleme, `retention_days` sabiti veya yönetim komutu yok.

`durum` alanı `ham`, `islendi`, `hata`, `atla` değerlerini alıyor ama `islendi` durumundaki satırlar silinmiyor — ebediyen birikmeye devam ediyor.

### 3) `hesap_yonetimi` sorgularında hassas veri

**Kanıt:** `hesap_yonetimi/views.py` → `firma_kartlari()`, `cari_detay()`, `hesap_hareketleri()` — cari e-posta, telefon, adres gibi alanlar Mikro ERP'den çekiliyor ancak bu veriler log'a düşebiliyor (`logger.debug()` çağrıları).

---

## Hedef standart

1. **Saklama süresi politikası**: `MikroFatura` → `islendi` durumuna geçtikten N gün sonra `ham_json` alanı temizlenir.
2. **Veri minimizasyonu**: `ham_json` içindeki gereksiz kişisel alanlar (e-posta, cep telefonu) import sonrası temizlenir veya hiç kaydedilmez.
3. **Log temizliği**: `logger.debug()` içinde hassas veri (`fat_cari_vkn`, e-posta, TC kimlik) log'a yazılmaz.
4. **Yönetim komutu**: `python manage.py veri_temizle --gun 90` ile eski kayıtları sil.

---

## Önerilen uygulama yaklaşımı

### 1. `ham_json` temizleme alanı ekle

```python
# mikro_gelen/models.py — EKLENECEKler
ham_json_temizlendi = models.BooleanField("Ham Veri Temizlendi", default=False)
```

### 2. Yönetim komutu

```python
# mikro_gelen/management/commands/veri_temizle.py
class Command(BaseCommand):
    help = "İşlenmiş faturaların ham verisini ve eski ham kayıtları temizler"

    def add_arguments(self, parser):
        parser.add_argument("--gun", type=int, default=90)

    def handle(self, *args, **options):
        sinir = date.today() - timedelta(days=options["gun"])
        # islendi olanların ham_json'unu temizle
        temizlenen = MikroFatura.objects.filter(
            durum="islendi", fat_tarih__lt=sinir, ham_json_temizlendi=False
        ).update(ham_json="", ham_json_temizlendi=True)
        self.stdout.write(f"{temizlenen} kaydın ham verisi temizlendi.")
```

### 3. Log güvenlik kuralı

```python
# YANLIŞ
logger.debug("Cari %s, VKN: %s", fat_cari_unvan, fat_cari_vkn)

# DOĞRU
logger.debug("Cari kod: %s", fat_cari_kod)  # yalnızca kod
```

### 4. `baslat.bat` içine periyodik temizleme

`baslat.bat` şu an migrate çalıştırıyor; ayrı bir `zamanlanmis_gorevler.bat` veya Windows Task Scheduler ile haftalık `veri_temizle --gun 90` koşulabilir.

---

## Kabul kriterleri

- `MikroFatura` → `ham_json` 90 gün sonra otomatik temizlenebilir (komut var)
- `logger.debug/info` çağrılarında VKN, e-posta, telefon log'a düşmüyor
- `veri_temizle` komutu `python manage.py` ile sorunsuz çalışıyor
- Temizleme işlemi yanlışlıkla canlı fatura verisini silmiyor (`islendi` + tarih kontrolü)

---

## Sonraki iş paketleri

- P1.1 — `mikro_gelen/management/commands/veri_temizle.py` yaz
- P1.2 — `ham_json_temizlendi` alanı + migration
- P1.3 — `hesap_yonetimi/views.py` log satırlarını tarıyarak hassas veri tespiti
- P2.1 — Windows Task Scheduler ile haftalık `veri_temizle`
