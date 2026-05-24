# Runbook 11 — KVKK, kişisel veri ve veri saklama

**Faz:** P0  
**Durum:** Tespit edildi, uygulanmadı

## Amaç

Muhasebe büroları doğası gereği müşterilerinin **kişisel verilerini** (ad, vergi/TC no, telefon, e-posta, adres, banka bilgisi) işler.
Bu runbook, projenin **6698 sayılı KVKK** uyumu için minimum gereksinimleri tanımlar; veri sızıntısı, hukuki risk ve müşteri güveninin kaybı sonuçlarını azaltır.

## Neden kritik

KVKK ihlali, Türkiye'de muhasebe bürosu sahibine ciddi idari para cezası ve cezai sorumluluk doğurur.
Yazılım "yerel" çalışıyor olması bu yükümlülüğü ortadan kaldırmaz — veriyi işleyen sistemin **veri güvenliğini sağlama** yükümlülüğü vardır.

## Mevcut durum ve kanıtlar

### 1) Kişisel veri envanteri yok

**Etkilenen modeller (örnek):**

- `cari/models.py` → `Cari.ad`, `vergi_no`, `telefon`, `email`, `adres`, `vergi_dairesi`
- `kullanici/models.py` → `User`, `AktiviteLogu` (IP dahil)
- `banka/models.py` → IBAN, hesap sahibi
- `ceksenet/models.py` → keşideci adı, banka şubesi
- `sozlesme/models.py` → müşteri bilgisi

**Eksik:**

- Hangi modelde hangi tür kişisel veri tutuluyor — yazılı envanter yok.
- Veri sahibi kategorisi (müşteri / tedarikçi / personel) ayrımı yok.
- Veri işleme amacı (faturalama, raporlama vb.) tanımlı değil.

### 2) Veri saklama / silme politikası yok

**Kanıt:**

- Tüm modeller verileri **süresiz** tutar.
- "Pasifleştirilen" cariler `aktif=False` ile işaretlenir ama silinmez.
- `AktiviteLogu` zaman sınırı olmaksızın büyür.

**Risk:**

- KVKK m.7 — amaca uygun saklama süresi sonunda silme/anonimleştirme zorunlu.
- Sınırsız büyüyen log → veri minimizasyonu ilkesini ihlal eder.

### 3) Veri sahibi hakları için mekanizma yok

**Eksik:**

- Kişisel verilerin **dışa aktarımı** (taşınabilirlik hakkı) için kullanıcı arayüzü yok.
- Belirli bir carinin tüm kişisel verisinin **silinmesi/anonimleştirilmesi** için fonksiyon yok.
- Cari soft-delete uygulansa bile veri içeriği değişmiyor (ad/telefon/email duruyor).

### 4) Veri tabanı şifrelenmemiş

**Kanıt:**

- `db.sqlite3` düz dosya — disk erişimi olan herkes okuyabilir.
- Yedek dosyaları (`dashboard/views.py:yedek_indir`) düz SQLite olarak indiriliyor.

**Risk:**

- Çalınan/kaybolan dizüstü → tüm müşteri verisi sızar.

### 5) Loglarda kişisel veri sızabilir

**Kanıt:**

- `mikro_sync/settings.py` log formatı düz metin.
- View'larda hata mesajları örnek değişken dökümü içerebilir (`logger.error("...", exc_info=True)`).
- `AktiviteLogu` IP adresi tutar — bu da kişisel veridir.

### 6) Aydınlatma metni / KVKK uyum belgesi yok

**Kanıt:**

- Repoda KVKK aydınlatma metni, VERBİS kaydı, veri envanteri veya saklama planı bulunmuyor.
- UI'da kullanıcıya gösterilen bir aydınlatma metni yok.

## Hedef standart

- Hangi alanın kişisel veri olduğu **kod seviyesinde işaretli** olmalı.
- Her veri kategorisi için **saklama süresi** tanımlı olmalı.
- Süre sonunda **otomatik anonimleştirme / silme** çalışmalı.
- Veri sahibi talebi geldiğinde **tek komutla dışa aktarım ve silme** mümkün olmalı.
- Yedek dosyaları **şifrelenmiş** dışarı çıkmalı.
- Loglarda kişisel veri **maskelenmiş** olmalı.

## Önerilen uygulama yaklaşımı

1. **Veri envanteri çıkar:** `docs/kvkk/veri-envanteri.md` — model × alan × veri tipi × saklama süresi.
2. **Saklama süresi tanımla:** ör. `AktiviteLogu` için 6 ay, ticari belgeler için VUK gereği 5 yıl.
3. **Yönetim komutu yaz:** `python manage.py kvkk_temizle` — süresi dolmuş kayıtları anonimleştirir.
4. **Cari için anonimleştirme aksiyonu:** `cari_anonimlestir(cari)` → ad="Silinen Cari #N", telefon/email/adres temizlenir, finansal kayıt tarih+tutar korunur (VUK gereği).
5. **Veri sahibi dışa aktarım view'ı:** seçili cariye ait tüm veriyi JSON/PDF olarak indir.
6. **Yedekleri şifrele:** `yedek_indir()` parolalı ZIP veya `cryptography.fernet` ile şifrele (bkz. runbook 07).
7. **Log maskeleme filtresi ekle:** `logging.Filter` ile TC/vergi no/IBAN/e-posta düz metin yazılmasın.
8. **Aydınlatma metni şablonu** ekle ve login sonrası tek seferlik gösterim onayı al.

## Kabul kriterleri

- `docs/kvkk/` altında envanter ve saklama planı yazılı.
- Saklama süresi dolmuş loglar otomatik temizleniyor.
- Bir cari için "veriyi anonimleştir" işlemi UI'dan çalıştırılabilir ve geri alınamaz şekilde uyarı verir.
- Yedek dosyaları parolasız okunamaz.
- Loglarda tam vergi no/TC/IBAN çıktısı bulunmaz (regex maskeleme testi geçer).

## Sonraki iş paketleri

- P0.6 — Veri envanteri ve saklama planı belgele
- P0.7 — Cari anonimleştirme + dışa aktarım fonksiyonları
- P1.19 — Yedek şifreleme (runbook 07 ile birlikte)
- P1.20 — Log maskeleme filtresi
