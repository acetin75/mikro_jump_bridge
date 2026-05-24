# Mikro Jump Bridge — Kurulum Kılavuzu

## Gereksinimler

| Gereksinim | Sürüm | Not |
|---|---|---|
| Python | 3.10 veya üzeri | [python.org](https://www.python.org/downloads/) — "Add Python to PATH" seçili olmalı |
| Git | Herhangi | Opsiyonel (indirme ile kurulabilir) |
| Mikro ERP | Herhangi | API servisi açık ve erişilebilir olmalı |
| İşletim Sistemi | Windows 10/11 | |

---

## Kurulum

### 1. Projeyi İndirin

**Git ile:**
```bat
git clone https://github.com/acetin75/mikro_jump_bridge.git
cd mikro_jump_bridge
```

**ZIP ile:** GitHub'dan ZIP indirip çıkartın.

---

### 2. `.env` Dosyasını Oluşturun

Proje kökünde `.env` dosyası oluşturun:

```
SECRET_KEY=buraya-en-az-50-karakterlik-rastgele-bir-deger-yazin
DEBUG=False
ALLOWED_HOSTS=127.0.0.1,localhost

# Admin hesabı (baslat.bat otomatik oluşturur)
ADMIN_KULLANICI=admin
ADMIN_SIFRE=GucluBirSifre123!

# Lisans imzalama anahtarı (sadece GELİŞTİRİCİ kurar — müşteriye verilmez)
# LISANS_IMZA_ANAHTARI=kendi-gizli-anahtariniz
```

> **Not:** `SECRET_KEY` için rastgele değer üretmek:
> ```bat
> python -c "import secrets; print(secrets.token_urlsafe(50))"
> ```

---

### 3. Uygulamayı Başlatın

```bat
baslat.bat
```

Bu komut:
- Python sanal ortamı oluşturur (`.venv`)
- Gerekli paketleri kurar (`requirements.txt`)
- Veritabanı tablolarını hazırlar (`migrate`)
- Admin kullanıcısını oluşturur (`.env`'deki bilgilerle)
- Sunucuyu `http://127.0.0.1:8001` adresinde başlatır

---

## İlk Giriş

1. Tarayıcıda `http://127.0.0.1:8001` adresini açın
2. `.env`'deki `ADMIN_KULLANICI` ve `ADMIN_SIFRE` ile giriş yapın

---

## Mikro ERP Bağlantısı

Uygulama Mikro ERP'ye **sadece okuma** modunda bağlanır. Her firma için ayrı bir **Firma Ayarı** kaydı oluşturulur.

1. `http://127.0.0.1:8001/admin/` adresine gidin
2. **Sync Motor → Firma Ayarları → Ekle** butonuna tıklayın
3. Aşağıdaki bilgileri doldurun.

### Temel Alanlar

| Alan | Açıklama | Örnek |
|---|---|---|
| Firma Adı | Açıklama amaçlı | `Örnek A.Ş.` |
| Aktif | Bağlantıyı etkinleştir | ✅ |
| Bağlantı Tipi | `Mikro API` / `SQL Server` / `Manuel XML` | `Mikro API` |
| Firma Kodu | Mikro firma kodu | `MORE` |
| Çalışma Yılı | Sorgulanacak yıl | `2026` |
| Notlar | Serbest açıklama | — |

### Bağlantı Tipi: Mikro API (önerilen)

Mikro Desktop API servisi (`services.msc` → "Mikro Desktop API") üzerinden bağlanır. Her istekte günlük MD5 hash auth gönderilir.

| Alan | Açıklama | Örnek |
|---|---|---|
| **Yerel LAN IP** | Mikro sunucusunun yerel ağ IP'si | `192.168.1.10` |
| **FortiClient VPN IP** | VPN üzerinden bağlanıyorsanız VPN IP'si | `10.8.0.5` |
| **Uzak Masaüstü IP** | RDP ile sunucudaysanız genellikle `127.0.0.1` | `127.0.0.1` |
| API Port | Mikro API portu | `8094` (varsayılan) |
| Mikro Kullanıcı | Mikro kullanıcı adı | `SRV` |
| Mikro Şifre | Mikro şifresi (şifrelenip saklanır) | `****` |
| Mikro API Key | Mikro'nun talep ettiği API anahtarı (opsiyonel) | — |

> Üç IP alanından **dolu olanlar** "Bağlantı Testi" ekranında ayrı butonlar olarak görünür. Hangisi başarılı yanıt verirse o mod aktif olur.

#### Mikro API Servisi Kontrolü

Sunucu tarafında:
- `services.msc` → **Mikro Desktop API** servisi çalışıyor olmalı
- Varsayılan port: `8094`
- Port değişikliği: `regedit` → `HKLM\SYSTEM\CurrentControlSet\Services\MikroDesktopAPIContainer\Parameters\Port`
- Test: tarayıcıdan `http://<sunucu-ip>:8094/Api/APIMethods/` adresine erişim kontrol edin

### Bağlantı Tipi: SQL Server (alternatif)

Mikro API kapalı veya kullanılamıyorsa Mikro veritabanına doğrudan SQL Server bağlantısı kurulabilir.

| Alan | Açıklama | Örnek |
|---|---|---|
| SQL Sunucu | SQL Server adresi (instance dahil) | `192.168.1.10\SQLEXPRESS` |
| SQL Veritabanı | Mikro veritabanı adı | `MikroDB_V16_MORE` |
| SQL Kullanıcı | SQL kullanıcı adı | `sa` |
| SQL Şifre | SQL şifresi (şifrelenip saklanır) | `****` |

> SQL bağlantısı için Windows üzerinde `ODBC Driver 17 for SQL Server` veya üstü gereklidir.

### Bağlantı Tipi: Manuel XML

API ve SQL erişimi yoksa Mikro'dan XML dışa aktarımıyla manuel besleme yapılır (sınırlı kullanım — sadece okumayı temsil eder).

### Bağlantıyı Test Et

Kaydettikten sonra firma listesinde **Bağlantı Testi** butonuna tıklayın. Dolu olan IP modlarının her biri için sağlık kontrolü çalışır ve sonuç görüntülenir.

> Şifreler veritabanında `django.core.signing.Signer` ile imzalı saklanır. `SECRET_KEY` değiştiğinde imzalar geçersiz olur; bu durumda firma ayarından şifreyi tekrar girmek gerekir.

---

## Lisans

### Deneme Süresi

Uygulama ilk kurulumdan itibaren **15 gün ücretsiz** olarak çalışır.
Deneme süresi boyunca tüm özellikler kullanılabilir.

Kalan deneme süresi her sayfanın üstünde gösterilir.

### Lisans Satın Alma

Deneme süresi bittikten sonra uygulamayı kullanmaya devam etmek için lisans gereklidir.

1. Lisans için iletişime geçin: **ali.cetin@malihaber.com.tr**
2. Ödeme sonrasında size bir lisans anahtarı iletilir
3. `http://127.0.0.1:8001/lisans/` adresine gidin
4. Aldığınız anahtarı ilgili alana yapıştırın ve **Aktifleştir** butonuna tıklayın

### Lisans Türleri

| Tür | Süre | Özellikler |
|---|---|---|
| Standart | 1 yıl | Tüm özellikler |
| Premium | 1 yıl | Tüm özellikler + öncelikli destek |

---

## Yedekleme

Tüm veriler `db.sqlite3` dosyasındadır. Yedek almak için bu dosyayı kopyalayın:

```bat
copy db.sqlite3 db_yedek_%date:~6,4%%date:~3,2%%date:~0,2%.sqlite3
```

`.env` dosyasını da ayrıca yedekleyin (şifreler ve ayarlar burada saklanır).

---

## Sorun Giderme

| Sorun | Çözüm |
|---|---|
| `Sunucu başlamıyor` | `.env` dosyasının varlığını ve `SECRET_KEY` değerinin `django-insecure-` ile başlamadığını kontrol edin |
| `Mikro bağlantısı kurulamıyor` | Sunucu IP, port ve kullanıcı bilgilerini kontrol edin; Mikro API servisinin çalıştığından emin olun |
| `Lisans süresi doldu` | `http://127.0.0.1:8001/lisans/bitti/` adresinden yeni lisans anahtarı girin |
| `Şifre hatalı` | `.env` dosyasındaki `ADMIN_SIFRE` değerini değiştirin ve `baslat.bat` yeniden çalıştırın |
