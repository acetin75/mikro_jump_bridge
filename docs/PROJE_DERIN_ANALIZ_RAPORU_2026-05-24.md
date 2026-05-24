# Mikro Jump Bridge — Derin Proje Analiz Raporu

**Tarih:** 24 Mayıs 2026  
**Kapsam:** `c:\mikro_jump_bridge` çalışma alanı  
**Amaç:** Projeyi baştan sona inceleyip eksik, hatalı ve geliştirilmesi gereken noktaları fazlara ayırmak.  
**Not:** Bu rapor düzeltme yapmaz; sonraki adımlarda faz faz uygulanacak iş listesidir.

---

## 1. Yönetici Özeti

Projenin temel mimarisi doğru yönde: Django 5.2 LTS, SQLite, çok firmalı `FirmaAyar`, Mikro API için merkezi `MikroApiClient`, oturum tabanlı aktif firma seçimi ve read-only hesap yönetimi yaklaşımı iyi kurulmuş. Şifrelerin ham olarak veritabanına yazılmaması, `.env` tek otorite yaklaşımı, CI/release workflow'larının varlığı ve runbook dokümantasyonu güçlü taraflar.

Buna karşılık aşağıdaki alanlar öncelikli iyileştirme gerektiriyor:

| Öncelik | Kategori | Özet |
|---|---|---|
| P0 | Test/CI | Mevcut test paketi 2 hata ile kırılıyor: `ImportLog()` eski `yon` alanını bekliyor. |
| P0 | Release/Installer | `installer/setup.iss` olmayan `static\*` klasörünü paketlemeye çalışıyor; tag release derlemesi kırılabilir. |
| P1 | Güvenlik | `SECRET_KEY` yalnızca `django-insecure-` prefix'i için fail-fast yapıyor; `.env.example` placeholder'ı ve kısa/öngörülebilir anahtarlar üretimde yakalanmıyor. |
| P1 | Güvenlik | `olustur_admin.py`, `.env` içindeki zayıf/placeholder `ADMIN_SIFRE` değerini sessizce kabul ediyor. |
| P1 | Güvenlik | `hesap_yonetimi.firma_sec`, doğrulanmamış `next` değerine `redirect(next_url)` yapıyor; açık yönlendirme riski var. |
| P1 | Veri Güvenliği | `hesap_yonetimi` ve posta komutlarında SQL string interpolation yaygın; escape yalnızca tek tırnak düzeyinde. |
| P1 | Posta Güvenliği | `_EsnekSMTPBackend` sertifika doğrulamasını her zaman kapatıyor; bu davranış ayarlanabilir olmalı. |
| P1 | Test Kapsamı | Kritik katmanlar için test yok: `MikroApiClient`, middleware, lisans HMAC, posta gönderimi, açık redirect. |
| P2 | Mimari | `LisansBilgisi` ve `MailAyar` singleton varsayımları DB constraint ile korunmuyor. |
| P2 | Dokümantasyon | README/KURULUM bazı özellikleri mevcut koddan ileri gösteriyor: PDF/Excel/CSV çıktıları, log rotasyon standardı vb. |
| P2 | Frontend | `base.html` ve `firma_sec.html` içinde yoğun inline CSS/JS var; bakım maliyetini artırıyor. |

---

## 2. Çalıştırılan Kontroller

Aşağıdaki kontroller bu rapor hazırlanırken çalıştırıldı:

| Kontrol | Sonuç | Not |
|---|---|---|
| `python manage.py check` | Başarılı | Sistem kontrolünde hata yok. |
| `python manage.py test --verbosity 2` | Başarısız | 12 test bulundu, 10 geçti, 2 hata aldı. |
| `ruff check . --output-format=concise` | Başarılı | Ruff hata üretmedi. |
| `python manage.py check --deploy` | Uyarılı | `SECURE_HSTS_SECONDS` ve `SECURE_SSL_REDIRECT` uyarıları var. Lokal/HTTP kullanım nedeniyle bilinçli olabilir. |
| `pip-audit -r requirements.txt` | Başarılı | Bilinen güvenlik açığı bulunmadı. |
| `vulture ... --min-confidence 80` | Hata üretmedi | Yüksek güvenli ölü kod bulgusu raporlanmadı. |

### Test Hatası Detayı

Dosya: `sync_motor/tests.py`

`ImportLogTestleri.setUp()` içinde `ImportLog.objects.create(..., yon="mikro_to_mb", ...)` çağrılıyor. Ancak güncel `sync_motor.models.ImportLog` modelinde `yon` alanı yok. Test paketi bu nedenle iki testte `TypeError: ImportLog() got unexpected keyword arguments: 'yon'` hatası alıyor.

**Öneri:** Faz 0'da test verisini güncel modele göre düzeltmek ve CI'yı yeniden yeşile almak.

---

## 3. Güçlü Taraflar

- `sync_motor.models.FirmaAyar` Mikro şifresini `django.core.signing` ile saklıyor; ham şifre DB'ye yazılmıyor.
- `MailAyar` SMTP şifresini ham tutmuyor, `Signer` ile imzalı saklıyor.
- `MikroApiClient` tek merkezde; auth, endpoint çağrısı ve hata yönetimi çoğunlukla burada toplanmış.
- `@login_required` kullanımı yaygın ve özel middleware ile giriş zorunluluğu destekleniyor.
- `kullanici.forms` Django password validator'lerini kullanıyor; kullanıcı ekleme/şifre değiştirme formları temel güvenlik açısından iyi.
- `requirements.txt` tam sürüm pin'li (`==`) ve `pip-audit` temiz.
- `.github/workflows/ci.yml` ve `.github/workflows/release.yml` mevcut; otomasyon temeli kurulmuş.
- Runbook dokümantasyonu kapsamlı ve proje standartlarını net anlatıyor.
- `yedek/`, `.env`, `db.sqlite3`, `.venv/` gibi hassas/yerel dosyalar `.gitignore` içinde.

---

## 4. Faz 0 — Hemen Düzeltilmesi Gereken Kırıklar

Bu fazın hedefi: **CI/test/release hattının kırık kalmaması.**

### 4.1 Test Paketi Kırık: `ImportLog.yon`

- **Dosya:** `sync_motor/tests.py`
- **Kanıt:** `python manage.py test --verbosity 2` çıktısında 2 hata.
- **Risk:** CI kırılır; sonraki refactor'larda güvenli ilerlemek zorlaşır.
- **Önerilen düzeltme:** `ImportLog.objects.create()` çağrısından `yon="mikro_to_mb"` alanını kaldır veya modelde gerçekten iş kuralı olarak gerekiyorsa alanı migration ile geri ekle. Mevcut kod yapısına göre kaldırmak daha doğru görünüyor.
- **Doğrulama:** `python manage.py test --verbosity 2` tüm testler geçmeli.

### 4.2 Installer Release Kırılma Riski: Olmayan `static` Klasörü

- **Dosya:** `installer/setup.iss`
- **Kanıt:** Workspace kökünde `static/` yok; yalnızca `staticfiles/` var. `setup.iss` içinde `Source: "..\static\*"` satırı bulunuyor.
- **Risk:** Inno Setup derlemesi kaynak dosya bulunamadığı için tag release sırasında kırılabilir.
- **Önerilen düzeltme seçenekleri:**
  1. Gerçekten statik kaynak klasörü kullanılacaksa `static/` oluştur ve paketle.
  2. Kullanılmayacaksa `setup.iss` satırını kaldır veya `skipifsourcedoesntexist` benzeri güvenli bir strateji uygula.
  3. Runtime `collectstatic` kullanılacaksa `staticfiles/` paketleme gereksinimini ayrıca değerlendir.
- **Doğrulama:** Release workflow veya lokal `ISCC.exe installer\setup.iss` derlemesi başarılı olmalı.

### 4.3 Release Gövdesindeki Varsayılan Şifre Metni

- **Dosya:** `.github/workflows/release.yml`
- **Kanıt:** Release notunda `Varsayılan kullanıcı: admin / Şifre: Admin1234!` yazıyor.
- **Risk:** Müşteri kurulumunda aynı varsayılan şifreyle bırakma alışkanlığı güvenlik riski yaratır.
- **Öneri:** Release notunu “ilk kurulumda `.env` içinden üretilen/değiştirilmesi gereken admin bilgisi” şeklinde revize et; mümkünse installer ilk kurulumda güçlü şifre üretip kullanıcıya gösterme/değiştirtme akışı tasarla.

---

## 5. Faz 1 — Güvenlik ve Sır Yönetimi

Bu fazın hedefi: **üretime yanlış/placeholder sırlarla çıkmayı engellemek ve yönlendirme açıklarını kapatmak.**

### 5.1 `SECRET_KEY` Fail-Fast Yetersiz

- **Dosya:** `mikro_sync/settings.py`
- **Mevcut durum:** `DEBUG=False` iken sadece `SECRET_KEY.startswith("django-insecure-")` kontrol ediliyor.
- **Ek kanıt:** `.env.example` içinde `SECRET_KEY=buraya-guclu-uretilmis-anahtar-yazin` var. Bu değer `django-insecure-` ile başlamadığı için `DEBUG=False` ortamda kabul edilir.
- **Risk:** Placeholder veya zayıf anahtarla üretim başlar; imzalı şifreler, session ve lisans türetimi etkilenir.
- **Öneri:** `DEBUG=False` iken şu kontroller fail-fast olmalı:
  - `SECRET_KEY` boş olmamalı.
  - Bilinen placeholder kalıpları reddedilmeli: `buraya`, `degistir`, `change`, `default`, `test`, `ci-test` vb.
  - Minimum uzunluk kontrolü uygulanmalı; örn. 50+ karakter.
  - `.env.example` örneği gerçek üretim gibi algılanmamalı.
- **Doğrulama:** `DEBUG=False` + `.env.example` placeholder değeri ile uygulama başlamamalı.

### 5.2 Admin Şifresi Placeholder/Zayıf Değer Kabul Ediyor

- **Dosya:** `olustur_admin.py`
- **Mevcut durum:** `.env` içinde `ADMIN_SIFRE` tanımlıysa script sessiz çalışıyor; değerin güçlü olup olmadığı kontrol edilmiyor.
- **Risk:** `Admin1234!`, `admin123`, `buraya-yazin` gibi değerler üretimde kalabilir.
- **Öneri:**
  - `ADMIN_SIFRE` için placeholder ve çok zayıf örüntü denetimi ekle.
  - Django `validate_password()` kullan.
  - Sessiz modda zayıf şifre varsa exit code `1` ile dur.
  - Interaktif modda da aynı validator çalışmalı.
- **Doğrulama:** Zayıf şifreyle `olustur_admin.py` başarısız olmalı; güçlü şifreyle admin oluşturmalı/güncellemeli.

### 5.3 Açık Yönlendirme Riski: `firma_sec`

- **Dosya:** `hesap_yonetimi/views.py`, `templates/hesap_yonetimi/firma_sec.html`
- **Mevcut durum:** Şablon `request.GET.next` değerini hidden input'a koyuyor, view `return redirect(next_url)` çağırıyor.
- **Risk:** Kötü niyetli kullanıcı `next=https://...` gibi bir değerle açık yönlendirme yaratabilir. Bağlantı testi UI engeli olsa da crafted POST ile aşılabilir.
- **Öneri:**
  - `django.utils.http.url_has_allowed_host_and_scheme` ile `next` doğrula.
  - İzinli değilse `hy_panel` gibi güvenli varsayılan rotaya dön.
  - Tercihen yalnızca path/URL name whitelist kabul et.
- **Doğrulama:** `next=https://example.com` ile POST edildiğinde dış domaine redirect olmamalı.

### 5.4 SMTP Sertifika Doğrulaması Her Zaman Kapalı

- **Dosya:** `posta/utils.py`
- **Mevcut durum:** `_EsnekSMTPBackend.open()` içinde `ctx.check_hostname = False` ve `ctx.verify_mode = ssl.CERT_NONE` sabit.
- **Risk:** TLS şifreli kalsa bile sunucu kimliği doğrulanmaz; MITM riski artar.
- **Öneri:**
  - Bu davranışı `MailAyar` alanı veya `.env` bayrağı ile opsiyonel yap.
  - Varsayılan güvenli olsun: sertifika doğrulaması açık.
  - Eski/paylaşımlı hosting için “sertifika doğrulamayı kapat” seçeneği açık uyarı ile kullanılmalı.
- **Doğrulama:** Varsayılan backend doğrulama açık çalışmalı; özel ayarla eski davranış korunmalı.

### 5.5 Lisans İmza Anahtarı SECRET_KEY'den Türetiliyor

- **Dosya:** `lisans/utils.py`
- **Mevcut durum:** `LISANS_IMZA_ANAHTARI` yoksa `SECRET_KEY + "-lisans"` üzerinden imza anahtarı türetiliyor.
- **Risk:** Müşteri makinesindeki `SECRET_KEY` değişirse mevcut/gelecek lisans doğrulama davranışı karışabilir. Ayrıca geliştirici imza anahtarı ile müşteri runtime sırrı kavramsal olarak ayrılmalı.
- **Öneri:** Üretim/release için `LISANS_IMZA_ANAHTARI` zorunlu veya ayrı, belgelenmiş bir akış olsun. Müşteri tarafında imza üretme anahtarı bulunmamalıysa doğrulama mimarisi ayrıca gözden geçirilmeli.

---

## 6. Faz 2 — Veri Erişimi, Mikro API ve İş Mantığı Sağlamlaştırma

Bu fazın hedefi: **Mikro sorgularını güvenilir, test edilebilir ve bakımı kolay hale getirmek.**

### 6.1 Serbest SQL String Interpolation Yaygın

- **Dosyalar:**
  - `hesap_yonetimi/views.py`
  - `posta/views.py`
  - `posta/management/commands/ekstre_gonder.py`
  - `sync_motor/client.py`
- **Mevcut durum:** Kullanıcı girdileri veya Mikro cari kodları SQL string içine f-string ile gömülüyor; çoğu yerde sadece `'` → `''` escape yapılıyor.
- **Risk:** Mikro `SqlVeriOkuV2` parametrik sorgu desteklemiyorsa dahi injection yüzeyi tamamen kapanmış sayılmaz. Ayrıca sorgu üretimi view içinde büyüyor ve test zorlaşıyor.
- **Öneri:**
  - Merkezi bir `sql_escape_literal()` yardımcı fonksiyonu oluştur.
  - Tarih, sayı, enum ve kolon/order alanları için ayrı whitelist doğrulaması yap.
  - `order_by` gibi alanlarda mevcut `order_map` yaklaşımı sürdürülmeli.
  - Uzun SQL parçalarını servis katmanına taşı: `hesap_yonetimi/services.py` veya `queries.py`.
  - Mikro API parametrik SQL destekliyorsa buna geçiş araştırılmalı.
- **Doğrulama:** Tek tırnak, yüzde, köşeli parantez, noktalı virgül gibi girdilerle view testleri eklenmeli.

### 6.2 `MikroApiClient` Response Parsing Tekrarlı ve Kısmi

- **Dosya:** `sync_motor/client.py`
- **Mevcut durum:** `gelen_faturalar`, `cari_hesaplar`, `stok_kartlari` içinde farklı response wrapper anahtarları elle deneniyor. `sql_oku` ayrı parse ediyor.
- **Risk:** Mikro API sürüm farklarında sessiz boş liste dönebilir; hata görünmez.
- **Öneri:**
  - `_extract_list_response(response, preferred_keys)` gibi merkezi bir parser ekle.
  - Beklenmeyen formatta warning log'a response anahtarları yazılsın; hassas veri loglanmasın.
  - `sql_oku` parse hatalarında sadece boş liste dönmek yerine debug edilebilir hata kodu/mesaj opsiyonu sağlansın.
- **Doğrulama:** Mock response formatlarıyla unit test yazılmalı.

### 6.3 Form Kaydetme Mantığı View'larda Dağınık

- **Dosyalar:** `sync_motor/forms.py`, `sync_motor/views.py`, `posta/forms.py`, `posta/views.py`
- **Mevcut durum:** Şifre alanını kaydetme ve ilk kayıtta şifre zorunluluğu view içinde yapılıyor.
- **Risk:** Aynı form başka view/akışta kullanılırsa şifre işleme unutulabilir.
- **Öneri:**
  - `FirmaAyarForm.save()` içinde `mikro_sifre_gir` işleme merkezileştirilsin.
  - `MailAyarForm.clean_sifre()` ve/veya `save()` ile ilk kayıt şifre zorunluluğu forma taşınsın.
  - View sadece `form.save()` ve mesaj/redirect ile ilgilensin.
- **Doğrulama:** Form unit testleri eklensin.

### 6.4 Singleton Varsayımları DB ile Korunmuyor

- **Dosyalar:** `lisans/models.py`, `lisans/views.py`, `lisans/middleware.py`, `posta/models.py`, `posta/utils.py`
- **Mevcut durum:** `LisansBilgisi.objects.first()` ve `MailAyar.objects.filter(aktif=True).first()` kullanılıyor.
- **Risk:** Birden fazla kayıt oluşursa hangi kaydın geçerli olduğu belirsizleşir.
- **Öneri:**
  - `LisansBilgisi` için tek kayıt stratejisi belirle: sabit pk, singleton helper, DB constraint veya sistem ayarı modeli.
  - `MailAyar.save()` içinde aktif kayıt tekilliği sağlanabilir; aktif olan kaydedilince diğerleri pasife çekilebilir.
  - `mail_ayar_al()` ve `_lisans_al()` tek otorite helper olarak kullanılmalı.
- **Doğrulama:** Birden fazla kayıt senaryosu test edilmeli.

### 6.5 Para Hesaplarında `float` Kullanımı

- **Dosyalar:** `hesap_yonetimi/views.py`, `posta/views.py`, `posta/management/commands/ekstre_gonder.py`
- **Mevcut durum:** Mikro'dan gelen tutarlar birçok yerde `float(...)` ile işleniyor.
- **Risk:** Finansal ekstre/bakiye hesaplarında yuvarlama hassasiyeti bozulabilir.
- **Öneri:** Python tarafında `Decimal` kullan; şablonlarda formatlama yine `floatformat` veya özel filter ile yapılabilir.
- **Doğrulama:** Kümülatif bakiye hesapları için Decimal testleri eklenmeli.

---

## 7. Faz 3 — Test Stratejisi ve Kalite Kapıları

Bu fazın hedefi: **regresyonları yakalayan güvenilir test tabanı oluşturmak.**

### 7.1 Mevcut Test Kapsamı Dar

- **Mevcut durum:** 12 test var; ağırlık `sync_motor` model/view giriş kontrollerinde.
- **Eksik kritik testler:**
  - `MikroApiClient._sifre_hash()` formatı ve günlük hash davranışı.
  - `_post()` için timeout, connection error, HTTP error, invalid JSON, API `Hata` response.
  - `sql_oku()` response parse varyasyonları.
  - `FirmaSecimZorunluMiddleware` yönlendirme davranışı.
  - `LisansKontrolMiddleware` deneme süresi doldu/aktif lisans senaryoları.
  - `lisans_anahtari_uret/dogrula` HMAC doğrulama testleri.
  - `posta.utils.ekstre_gonder` mock mail backend ile başarı/hata logu.
  - `firma_sec` açık redirect engelleme testi.
- **Öneri:** Testleri uygulama bazında ayır: `test_models.py`, `test_forms.py`, `test_views.py`, `test_client.py`, `test_middleware.py`.

### 7.2 CI Eksikleri

- **Dosya:** `.github/workflows/ci.yml`
- **Mevcut durum:** requirements kuruluyor, Ruff, Django check ve test çalışıyor.
- **Eksikler:**
  - `requirements-dev.txt` kurulmadığı halde `ruff` komutu kullanılıyor; GitHub hosted runner üzerinde ruff hazır değilse CI kırılabilir. CI'da `pip install -r requirements-dev.txt` veya en az `ruff` kurulmalı.
  - `pip-audit` CI'da yok.
  - `ruff format --check` CI'da yok.
  - `check --deploy` CI'da yok; lokal `kontrol.bat` çalıştırıyor.
- **Öneri:** CI ile `kontrol.bat` arasında kalite kapılarını uyumlu hale getir.

### 7.3 `kontrol.bat` Hata Yönetimi

- **Dosya:** `kontrol.bat`
- **Mevcut durum:** Komutlar ardışık çalışıyor; herhangi bir adım hata verse bile betik devam ediyor ve sonunda “TAMAMLANDI” yazıyor.
- **Risk:** Commit öncesi kalite kapısı yanlış güven verebilir.
- **Öneri:** Her komut sonrası `if errorlevel 1 exit /b 1` eklenmeli; son mesaj “başarılı tamamlandı” yalnızca tüm adımlar geçtiyse yazılmalı.

---

## 8. Faz 4 — Deployment, Installer ve Operasyon

Bu fazın hedefi: **müşteri kurulumunu tekrarlanabilir ve güvenli hale getirmek.**

### 8.1 Installer `.env.example` / `env.example` Akışı Karışık

- **Dosyalar:** `.github/workflows/release.yml`, `installer/setup.iss`, `installer/baslat_kurulu.bat`
- **Mevcut durum:** Release workflow `.env.example` dosyasını `env.example` olarak kopyalıyor. `setup.iss`, `env.example` dosyasını `.env` adıyla kuruyor. `baslat_kurulu.bat` ise `.env` yoksa `.env.example` arıyor.
- **Risk:** Kurulum sonrası `.env` silinirse launcher yeniden oluşturamayabilir; dosya adları ekip için kafa karıştırıcı.
- **Öneri:** Tek isim stratejisi seç:
  - Kaynakta `.env.example` kalsın.
  - Installer içinde ya `.env.example` da paketlensin ya da launcher `env.example` arayacak şekilde güncellensin.

### 8.2 `baslat.bat` Admin Hatasını Uyarı Olarak Geçiyor

- **Dosya:** `baslat.bat`
- **Mevcut durum:** `olustur_admin.py` hata verirse “UYARI” yazıp devam ediyor.
- **Risk:** İlk kurulumda admin oluşturulmazsa kullanıcı uygulamaya giremeyebilir.
- **Öneri:** İlk kurulumda admin oluşturma başarısızsa durmalı; yalnızca mevcut admin varsa devam edilebilir. Bu ayrımı script veya Python tarafında açıkça yönet.

### 8.3 Deploy Check Uyarıları Bilinçli Şekilde Yönetilmeli

- **Dosya:** `mikro_sync/settings.py`
- **Kanıt:** `manage.py check --deploy` şu uyarıları verdi:
  - `security.W004`: `SECURE_HSTS_SECONDS` ayarlı değil.
  - `security.W008`: `SECURE_SSL_REDIRECT` True değil.
- **Yorum:** Uygulama çoğunlukla `127.0.0.1:8001` lokal Windows aracı olarak çalışıyorsa bu uyarılar bilinçli kabul edilebilir. Ancak LAN/uzak erişim senaryosu varsa reverse proxy + HTTPS standardı belgelenmeli.
- **Öneri:** Runbook'ta “lokal kurulum” ve “LAN/HTTPS üretim” profillerini ayır.

### 8.4 Log Rotasyon Standardı Dokümantasyonla Uyuşmuyor

- **Dosyalar:** `mikro_sync/settings.py`, `.github/copilot-instructions.md`, README/runbook metinleri
- **Mevcut durum:** Settings `TimedRotatingFileHandler` ile 30 günlük rotasyon kullanıyor. Proje talimatlarında “10 MB × 3 yedek” standardı geçiyor.
- **Risk:** Operasyon beklentisi ile gerçek davranış farklı.
- **Öneri:** Ya kodu `RotatingFileHandler(maxBytes=10MB, backupCount=3)` standardına döndür ya da dokümantasyonu “günlük rotasyon, 30 gün” diye güncelle.

---

## 9. Faz 5 — Dokümantasyon, Ürün Kapsamı ve UX

Bu fazın hedefi: **dokümanın gerçek ürünle birebir uyumlu olması ve UI bakım maliyetinin azalması.**

### 9.1 README Özellik Listesi Koddan İleri

- **Dosya:** `README.md`
- **Mevcut durum:** “PDF / Excel / CSV — Türkçe karakter destekli rapor çıktıları” özelliği listeleniyor.
- **Kanıt:** Kod taramasında `xhtml2pdf`, `openpyxl`, `csv` export veya ilgili `HttpResponse(content_type=...)` kullanımı bulunmadı. `requirements.txt` içinde `xhtml2pdf` veya `openpyxl` yok.
- **Risk:** Kullanıcı beklentisi oluşur fakat özellik yoktur.
- **Öneri:**
  - Özellik henüz yoksa README'de “planlanan” olarak işaretle veya kaldır.
  - Uygulanacaksa ayrı fazda PDF/Excel/CSV export tasarımı yap.

### 9.2 `defusedxml` Bağımlılığı Kullanılmıyor Görünüyor

- **Dosya:** `requirements.txt`, `sync_motor/client.py`
- **Mevcut durum:** `defusedxml==0.7.1` pin'li; `fatura_xml()` XML string döndürüyor fakat parse yok.
- **Risk:** Gereksiz bağımlılık veya yarım kalmış XML güvenlik hedefi.
- **Öneri:** XML parse edilecekse `defusedxml` ile güvenli parse yardımcıları ekle; edilmeyecekse bağımlılığı ve dokümanı gözden geçir.

### 9.3 Inline CSS/JS Yoğunluğu

- **Dosyalar:** `templates/base.html`, `templates/hesap_yonetimi/firma_sec.html`
- **Mevcut durum:** Layout stilleri ve firma seçim JS'i şablon içinde.
- **Risk:** Bakım ve yeniden kullanım zorlaşır; CSP uygulamak ileride zorlaşır.
- **Öneri:**
  - `static/css/app.css` ve `static/js/firma_sec.js` gibi dosyalara taşı.
  - Bootstrap değişkenleri/CSS custom properties kullan.
  - CSP hedeflenecekse inline script/style azaltılmalı.

### 9.4 Sidebar Mesajları Çift Görünebilir

- **Dosya:** `templates/base.html`
- **Mevcut durum:** `messages` hem topbar badge olarak hem içerikte alert olarak render ediliyor.
- **Risk:** Aynı mesaj iki kez görünebilir.
- **Öneri:** Mesaj gösterimini tek alana indir veya topbar'ı yalnızca özet/son mesaj için ayrı tasarla.

---

## 10. Önerilen Uygulama Sırası

### Faz 0 — Kırıkları Kapat (0.5 gün)

1. `sync_motor/tests.py` içindeki `yon` alanı hatasını düzelt.
2. Tüm testleri çalıştır ve CI'yı yeşile al.
3. `installer/setup.iss` içindeki olmayan `static\*` kaynak satırını düzelt.
4. Release workflow'un minimum bir tag dry-run mantığını doğrula.

### Faz 1 — Güvenlik Sertleştirme (1 gün)

1. `SECRET_KEY` placeholder/uzunluk fail-fast kontrolünü genişlet.
2. `olustur_admin.py` için güçlü şifre validasyonu ekle.
3. `firma_sec` `next` yönlendirmesini güvenli hale getir.
4. SMTP sertifika doğrulamasını varsayılan güvenli/opsiyonel esnek moda çek.

### Faz 2 — Servis ve Veri Katmanı (2-3 gün)

1. SQL escape/whitelist yardımcılarını merkezi hale getir.
2. Uzun Mikro SQL sorgularını servis/queries katmanına taşı.
3. `MikroApiClient` response parser'ını ortaklaştır.
4. `FirmaAyarForm` ve `MailAyarForm` şifre kaydetme/validasyon mantığını forma taşı.
5. Singleton modeller için net veri bütünlüğü stratejisi belirle.

### Faz 3 — Test Kapsamı ve CI (2 gün)

1. `MikroApiClient` mock testleri ekle.
2. Middleware, lisans, posta ve redirect güvenlik testleri ekle.
3. CI'da `requirements-dev.txt`, `ruff format --check`, `pip-audit` ve gerekirse `check --deploy` profili ekle.
4. `kontrol.bat` hata olduğunda duracak hale getir.

### Faz 4 — Operasyon ve Installer (1-2 gün)

1. `.env.example` / `env.example` kurulum akışını sadeleştir.
2. Admin oluşturma başarısızlığında başlatıcı davranışını netleştir.
3. Lokal/HTTPS deployment profillerini dokümante et.
4. Log rotasyon standardını kod ve dokümanda eşitle.

### Faz 5 — Dokümantasyon ve UI Temizliği (1-2 gün)

1. README/KURULUM özellik listesini gerçek kodla hizala.
2. PDF/Excel/CSV ya uygulanacak faza alınsın ya da “planlanan” olarak işaretlensin.
3. Inline CSS/JS statik dosyalara çıkarılsın.
4. Mesaj gösterimi tekilleştirilsin.

---

## 11. Fazlara Göre Kabul Kriterleri

| Faz | Kabul Kriteri |
|---|---|
| Faz 0 | `manage.py test`, `manage.py check`, `ruff check` geçer; installer source hatası yoktur. |
| Faz 1 | Placeholder sırlarla üretim başlamaz; açık redirect testi geçer; SMTP doğrulama davranışı belgelenir. |
| Faz 2 | SQL üretimi merkezi helper/servislerden geçer; kritik response parser testleri geçer. |
| Faz 3 | CI lokal `kontrol.bat` ile uyumludur; test paketi client/middleware/lisans/posta akışlarını kapsar. |
| Faz 4 | Release kurulumu temiz makinede tekrarlanabilir; `.env` ve admin akışı net çalışır. |
| Faz 5 | README/KURULUM/runbook gerçek ürün davranışıyla uyumludur; ana inline CSS/JS azaltılmıştır. |

---

## 12. Kısa Sonuç

Proje sağlam bir MVP/erken üretim tabanına sahip; asıl riskler mimari çöküşten çok **kalite kapısının kırık olması**, **sır yönetimi sertliğinin eksik kalması**, **installer/release küçük ama kritik uyumsuzlukları** ve **SQL/view mantığının zamanla büyümesi** tarafında. İlk iki faz tamamlandığında proje daha güvenli ve sürdürülebilir bir zemine oturur; sonraki fazlar bakım maliyetini ve regresyon riskini düşürür.
