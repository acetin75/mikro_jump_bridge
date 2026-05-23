# Muhasebe Bürosu — Monetizasyon & Geliştirme Planı

## Hedef

Yerel muhasebe büroları için kullanılan bu uygulamayı, GitHub üzerinde
açık kaynak olarak yayınlayarak hem topluluk hem de gelir elde etmek.

---

## Kararlar (22 Mayıs 2026)

| Konu | Karar |
|---|---|
| **Lisans** | **MIT** — herkes serbestçe kullanabilir |
| **Müşteri dosyaları** | `_arsiv/` klasörüne taşı, `.gitignore`'a ekle |
| **Uygulama sırası** | 1 → 2 → 3 → 4 → 5 |
| **Dağıtım Modeli** | **Model 1 — İndir & Çalıştır** (bkz. aşağı) |

---

## Dağıtım Modeli Kararı

### Model 1: İndir & Kendi Makinesinde Çalıştır ✅ SEÇİLDİ

```
GitHub → Kullanıcı indirir → Kendi bilgisayarına kurar → Kendi çalıştırır
```

| Özellik | Durum |
|---|---|
| Sunucu maliyeti | Sıfır — kullanıcının kendi makinesi |
| Veri güvenliği | Kullanıcının kendi bilgisayarında, biz sorumlu değiliz |
| Multi-tenancy | Gerekmiyor — her firma ayrı kurulum |
| Veritabanı | SQLite yeterli |
| Gelir modeli | Lisans / kurulum hizmeti / destek / özelleştirme |
| Mevcut koda uyum | %90 hazır, küçük iyileştirmeler yeterli |

### Model 2: SaaS (Benim Serverimdan Kullan) — ERTELENDI

Talep oluşursa değerlendirilebilir. Gereksinimler:
- Multi-tenancy (her firmaya `firma` FK'sı, tüm view'larda filtre)
- PostgreSQL + Railway/Render hosting (~$35/ay)
- Abonelik ödeme sistemi (iyzico/Stripe)
- +2-3 hafta geliştirme süresi

---

## Mevcut Durum Tespiti

### ✅ Zaten Hazır
- `.gitignore` — `db.sqlite3`, `logs/`, `.env`, `media/`, `__pycache__` dahil, eksiksiz
- `README.md` — kapsamlı; kurulum adımları, özellik listesi, teknoloji yığını mevcut
- `ceksenet/management/commands/hatirlatma_gonder.py` — çek/senet vade e-posta komutu çalışır durumda

### ⚠️ Eksikler
- `SECRET_KEY` `settings.py`'de hardcoded → `.env` + `python-decouple` gerekli
- `DEBUG = True` hardcoded → env var ile kontrol edilmeli
- `EMAIL_HOST_USER/PASSWORD` boş ama hardcoded → env var'a taşınmalı
- `HATIRLATMA_ALICI` `settings.py`'de hardcoded liste → env var'a taşınmalı
- `LICENSE` dosyası yok
- `python-decouple` `requirements.txt`'de yok
- Fatura vade hatırlatma management command yok (sadece çek var)

### 🚫 GitHub'a Gönderilmemesi Gereken Dosyalar (Müşteri Verisi)
Tümü `_arsiv/` klasörüne taşınacak:
- `Altıngüç Ltd_Şti_ _ Faturalar.msg` (+ 3 kopyası)
- `inceleme/` klasörü (tümü)
- `analiz_masraf.py`, `ayrilik_excel_uret.py`, `ikale_belgesi_uret.py`
- `rapor_uret.py`, `read_inceleme.py`, `extract_msgs.py`, `duzenle_gorsel.py`
- `AYRILIK_ANALIZI.md`
- (varsa) müşteriye ait `.xlsx`, `.pdf`, `.docx`, `.jpeg` dosyaları

---

## Aşama 1 — Temizlik & GitHub'a Hazırlık ✅ TAMAMLANDI

### Yapılacaklar
- [x] `.gitignore` — eksiksiz ✅
- [x] Müşteri dosyalarını `_arsiv/` klasörüne taşı, `.gitignore`'a `_arsiv/` ekle ✅
- [x] `requirements.txt`'e `python-decouple>=3.8` ekle ✅
- [x] `muhasebe_buro/settings.py` — `config()` ile env var oku ✅
- [x] `.env.example` oluştur ✅
- [x] `LICENSE` dosyası ekle — MIT ✅
- [x] `README.md` güncellendi ✅
- [x] `CONTRIBUTING.md` oluştur ✅
- [x] GitHub repository oluştur, ilk commit at ✅

---

## Aşama 2 — Katma Değerli Özellikler ✅ TAMAMLANDI

### 2.1 Dashboard Grafikleri (Chart.js) ✅
- [x] Aylık gelir/gider bar chart — son 6 ay
- [x] Cari tip dağılımı pasta grafik

### 2.2 Vade Hatırlatma Sistemi (E-posta) ✅
- [x] Çek/senet: `hatirlatma_gonder` management command (zaten mevcuttu)
- [x] Fatura: `fatura_hatirlatma` management command eklendi

### 2.3 Gelişmiş PDF Raporlar ⚠️ KISMI
- [x] Fatura PDF (xhtml2pdf ile)
- [ ] Müşteri ekstresi PDF (cari bazlı) — **YAPILMADI**
- [ ] Aylık/yıllık gelir-gider raporu PDF — **YAPILMADI**

### 2.4 Vergi Takvimi Modülü ✅
- [x] `takvim/` app — Türkiye vergi takvimi, renk kodlu badge, geri sayım

---

## Aşama 3 — Çoklu Kullanıcı & Yetki Sistemi ✅ TAMAMLANDI

### Yapılacaklar
- [x] Django `Group` sistemi — `Yönetici`, `Muhasebeci`, `Görüntüleyici` rolleri
- [x] `permissions.py` — `YetkiMiddleware` (URL pattern bazlı) + `AktiviteMiddleware`
- [x] Silme → sadece Yönetici; Düzenleme → Yönetici + Muhasebeci
- [x] `kullanici/` app — kullanıcı listesi, ekleme, rol atama
- [x] `AktiviteLogu` modeli — kim, ne zaman, hangi URL

---

## Aşama 4 — Model 1 Kullanıcı Deneyimi İyileştirmeleri ✅ BÜYÜK ÖLÇÜDE TAMAMLANDI

### 4.1 `baslat.bat` Geliştirme
- [x] `.venv` yoksa otomatik oluştur + `pip install -r requirements.txt`
- [x] Migration'ları otomatik çalıştır
- [x] Tarayıcıyı otomatik aç
- [ ] Port meşgulse alternatif port dene (8001, 8002...) — **YAPILMADI**

### 4.2 Sürüm Yönetimi ✅
- [x] `VERSION` dosyası → `1.0.0`
- [x] Footer'da sürüm numarası (`APP_VERSION` context processor)
- [ ] GitHub Releases ile etiketli sürüm yayınlama (git tag v1.0.0) — **YAPILMADI**

### 4.3 Yedek Alma Arayüzü ✅
- [x] Dashboard'da "Yedeği İndir" butonu (FileResponse)
- [x] Yedek geri yükleme (dosya yükle, Yönetici yetkisi ile)

### 4.4 Kurulum Kolaylaştırma ⚠️ EKSİK
- [ ] `KURULUM.md` — adım adım Windows kurulum rehberi — **YAPILMADI**
- [ ] `README.md`'ye ekran görüntüleri/GIF ekle — **YAPILMADI**

---

## Aşama 5 — E-Fatura Entegrasyonu ✅ BÜYÜK ÖLÇÜDE TAMAMLANDI

### Seçenekler
| Yöntem | Açıklama | Maliyet |
|---|---|---|
| **GİB Doğrudan** ✅ SEÇİLDİ | GİB Portal üzerinden XML yükleme | Ücretsiz |
| Özel Entegratör API | Foriba, Logo, Uyumsoft gibi entegratör | Aylık lisans |

### Yapılacaklar
- [x] `fatura/models.py` — `e_fatura_uuid`, `e_fatura_durum` alanları + migration
- [x] `fatura/efatura.py` — UBL-TR 2.1 formatında XML üretimi
- [x] Fatura detay sayfasında "E-Fatura XML İndir" butonu + durum badge
- [x] `fatura/urls.py` — `<pk>/xml/` endpoint
- [ ] Fatura PDF'ine e-arşiv QR kodu ekle (`qrcode` paketi kurulu, uygulama yok) — **YAPILMADI**
- [ ] `settings.py` + `.env.example` — `FIRMA_ADI`, `FIRMA_VKN`, `FIRMA_VERGI_DAIRESI`, `FIRMA_ADRES` — **YAPILMADI**

---

## Gelir Modeli Özeti (Güncel — v1.0.0+)

```
GitHub (açık kaynak, ücretsiz indir)
    ↓
Kurulum Hizmeti        → Bionluk / Fiverr (500-2.000₺ tek seferlik)
    +
Destek Paketi          → Aylık 200-500₺ — soru cevap, güncelleme
    +
Özelleştirme           → Kurumsal müşteri, logo/rapor/özel alan (saatlik 300-500₺)
    +
Çoklu Firma Modülü     → Muhasebe bürosu için ücretli eklenti (1.500-3.000₺)
    +
GitHub Sponsors        → Bireysel destek (aylık 5-50$)
    +
SaaS (gelecekte)       → Talep oluşursa Model 2'ye geçiş
```

### Hedef Kitle

> **2 farklı kullanıcı var:** Küçük işletme (kendi işini takip eder) ve Muhasebe Bürosu
> (müşterilerinin işini takip eder). Muhasebe Bürosu = Mali Müşavir = Muhasebeci — hepsi aynı şey.

| # | Kim | Ne İstiyor | Fiyat Modeli |
|---|---|---|---|
| 1 | **Küçük İşletme** | Kendi fatura/kasa/stok/çek takibini yapmak | Ücretsiz + kurulum hizmeti |
| 2 | **Muhasebe Bürosu** | Yönettiği 5-50 müşteri firmanın tümünü tek yerden görmek | Çoklu firma eklentisi (ücretli) |

---

## Öncelik Sırası (Güncel — 22 Mayıs 2026)

| # | Durum | Madde |
|---|---|---|
| 1 | ✅ TAMAMLANDI | GitHub'a hazırlık — `.env`, `.gitignore`, `LICENSE`, `README.md` |
| 2 | ✅ TAMAMLANDI | Dashboard grafikleri + vade hatırlatma + vergi takvimi |
| 3 | ✅ TAMAMLANDI | Çoklu kullanıcı & yetki sistemi |
| 4 | ✅ TAMAMLANDI | Model 1 UX — `VERSION`, yedek al/yükle, `baslat.bat`, `KURULUM.md` |
| 5 | ✅ TAMAMLANDI | E-fatura UBL-TR XML üretimi + QR kod + firma bilgileri |
| 6 | ✅ TAMAMLANDI | Stok & Ürün Yönetimi — CRUD + Ağırlıklı Ortalama + FIFO değerleme |
| 7 | ✅ TAMAMLANDI | Sürüm bildirimi (GitHub API) + Cari Mutabakat PDF + KDV Beyanname Excel |
| 8 | **[SIRADA]** | Kasa Defteri — günlük nakit takibi, kasa devir, nakit akış |
| 9 | **[SIRADA]** | Nakit Akış Tahmini + Müşteri Portali |
| 10 | **[PLANLANDI]** | Çoklu Firma (Mali Müşavirlik paketi) |

---

## Aşama 6 — Stok & Ürün Yönetimi ✅ TAMAMLANDI

### 6.1 Ürün & Hizmet Kartları (`stok/` app) ✅
- [x] `Urun` modeli: kod (otomatik UR0001…), ad, birim, kdv_orani, satis_fiyati, alis_fiyati, min_stok, aktif
- [x] `StokHareketi` modeli: urun FK, tip (giris/cikis/sayim), miktar, birim_fiyat, tarih, belge_no
- [x] Ürün listesi, ekle/düzenle/sil CRUD + kritik stok badge
- [x] Stok kartı sayfası: hareket geçmişi + mevcut bakiye + değerleme kartı

### 6.2 Stok Değerleme Yöntemleri (VUK Md.274) ✅
- [x] `stok/degerleme.py` — Ağırlıklı Ortalama (WAC) + FIFO hesap motoru
- [x] `Urun.degerleme_yontemi` alanı — ürün bazında yöntem seçimi
- [x] FIFO katman detayı (giriş tarihi, fiyat, kalan miktar)
- [x] Stok değerleme raporu sayfası + kâr marjı analizi
- [x] Excel export: özet sayfa + FIFO katman detay sayfası

### 6.3 Fatura ↔ Stok Entegrasyonu ✅ (Temel)
- [x] `FaturaKalemi.urun` FK opsiyonel → ürün kartı bağlantısı
- [ ] Satış faturası kaydedilince stok otomatik düşer — **İLERİ SÜRÜME ERTELENDI**
- [ ] Alış faturası kaydedilince stok otomatik artar — **İLERİ SÜRÜME ERTELENDI**

---

## Aşama 7 — Sürüm Bildirimi + Mali Müşavir Araçları ✅ TAMAMLANDI

### 7.1 Otomatik GitHub Sürüm Kontrolü ✅
- [x] `muhasebe_buro/surum_kontrol.py` — GitHub Releases API, 24 saat cache
- [x] `context_processors.py` — `yeni_surum_var/surum/url` tüm şablonlara
- [x] `settings.py` — `SURUM_KONTROL` config flag
- [x] `base.html` — Luca tarzı dismissible "Yeni sürüm mevcut" alert banner

### 7.2 Cari Mutabakat Mektubu ✅
- [x] `cari_mutabakat` view — dönem filtreli, bakiye hesaplamalı
- [x] A4 yazdırılabilir şablon: firma/cari bilgileri, hareket tablosu, imza alanı
- [x] Cari detay sayfasına "Mutabakat" butonu

### 7.3 KDV Beyanname Özeti (Excel) ✅
- [x] `excel_kdv_beyanname` view — hesaplanan / indirilecek / beyanname özeti (3 sayfa)
- [x] Yıl + ay filtresi, ödenecek/iade KDV hesabı

### 7.4 BA-BS Formu — KALDIRILDI
> Kullanıcı talebi doğrultusunda bu madde iptal edildi.

---

## Aşama 8 — Kasa Defteri

> **Neden kritik?** Türkiye'deki küçük işletmelerin %90'ı günlük nakit akışını
> defterle/Excel'le takip ediyor. Kasa defteri olmadan "muhasebe yazılımı"
> sayılmaz. Logo GO, Mikro, Luca'nın hepsinde var — rakipsiz bölge.
> Her iki hedef kitle de kullanır: küçük işletme kendi kasasını, muhasebe bürosu müşterisinin kasasını.

### 8.1 Kasa Modülü (`kasa/` yeni app)
- [ ] `KasaHesabi` modeli: ad, para_birimi, acilis_bakiyesi, aktif
- [ ] `KasaHareketi` modeli: kasa FK, tarih, tip (giris/cikis), tutar, aciklama, belge_no, kaynak (manuel/fatura/tahsilat/gider)
- [ ] Kasa listesi + bakiye gösterimi
- [ ] Günlük kasa defteri görünümü (giriş/çıkış/bakiye sütunlu)
- [ ] Kasa devir (dönem kapanış özeti)

### 8.2 Entegrasyonlar
- [ ] Tahsilat kaydedilince → kasa hareketi otomatik (opsiyonel)
- [ ] Gider ödenince → kasa hareketi otomatik (opsiyonel)
- [ ] Nakit fatura tahsilatı → kasa artışı

### 8.3 Dashboard Widget
- [ ] "Bugünkü Kasa Durumu" stat kartı
- [ ] Son 7 günlük kasa grafiği

### 8.4 Raporlar
- [ ] Günlük kasa raporu (Excel + yazdır)
- [ ] Aylık kasa özeti

---

## Aşama 9 — Nakit Akış Tahmini + Müşteri Portali

> **Neden farklılaştırıcı?** Hiçbir yerel muhasebe yazılımı bunu yapmıyor.
> "Önümüzdeki 30 günde kasanızdan ne çıkacak?" sorusunun cevabı.

### 9.1 Nakit Akış Tahmini Dashboard
- [ ] Gelecek 30/60/90 gün için outlook hesabı:
  - Vadesi gelen çekler (tahsil/ödeme)
  - Vadesi gelen faturaları (açık olanlar)
  - Tekrar eden giderler (geçmiş ortalamaya göre)
- [ ] Dashboard'da "Nakit Pozisyonu" kartı: Kasa + Banka + Vadeli Çek toplamı
- [ ] Uyarı: "30 gün içinde nakit açık oluşabilir" (eşik değer altına düşerse)

### 9.2 Müşteri Portali (Ücretsiz Farklılaştırıcı Özellik)
- [ ] Cari müşteriye özel token'lı link oluştur (`/portal/<token>/`)
- [ ] Müşteri login gerekmeden: kendi bakiyesini + açık faturalarını görebilir
- [ ] Fatura PDF indirebilir
- [ ] "Ödeme Yaptım" bildirimi gönderebilir (webhook veya e-posta)
- [ ] Token süresi: 30 gün (yenilenebilir)
- [ ] Rakiplerde yok → satış argümanı

---

## Aşama 10 — Çoklu Firma (Muhasebe Bürosu Paketi)

> **Neden?** Muhasebe bürosu (mali müşavir / muhasebeci) 5-50 müşteri firma yönetiyor.
> Her firma için ayrı kurulum = pratik değil. Çoklu firma desteği
> bu kullanıcıların ödeme yapmasını sağlayan kilit özellik.

### 10.1 Firma Modeli
- [ ] `Firma` modeli: ad, vkn, logo, iletişim bilgileri
- [ ] Tüm ana modellere `firma` FK eklenmesi (büyük migration)
- [ ] Middleware: `request.firma` otomatik set
- [ ] Sidebar'da firma seçici

### 10.2 Muhasebe Bürosu Arayüzü
- [ ] Müşteri firmaları listesi (ana dashboard)
- [ ] Firma bazlı dönem raporu (PDF — tek tuşla tüm özet)
- [ ] Firma bazlı vergi takvimi
- [ ] Toplu hatırlatma gönder (tüm firmalara)

### 10.3 Gelir Modeli
```
Küçük işletme (1 firma)     → Ücretsiz, açık kaynak
Çoklu firma modülü          → Ücretli eklenti (1.500-3.000₺ tek seferlik)
Muhasebe bürosu paketi      → Kurulum + destek + özelleştirme (5.000₺+)
```

---

## Kaynaklar

- [django-tenants](https://django-tenants.readthedocs.io/)
- [python-decouple](https://pypi.org/project/python-decouple/)
- [iyzico Geliştirici Docs](https://dev.iyzipay.com/)
- [GİB e-Belge API](https://ebelge.gib.gov.tr/)
- [Chart.js](https://www.chartjs.org/)
- [MIT Lisans](https://choosealicense.com/licenses/mit/)
