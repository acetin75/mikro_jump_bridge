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

1. `http://127.0.0.1:8001/admin/` adresine gidin
2. **Sync Motor → Firma Ayarları → Ekle** butonuna tıklayın
3. Aşağıdaki bilgileri doldurun:

| Alan | Açıklama | Örnek |
|---|---|---|
| Ad | Firma adı | Örnek A.Ş. |
| Mikro Sunucu | Mikro ERP sunucusunun IP adresi | `192.168.1.100` |
| Mikro Port | Mikro API port numarası | `8094` |
| Mikro Kullanıcı | Mikro kullanıcı adı | `ADMIN` |
| Mikro Şifre | Mikro şifresi | `****` |
| Firma Kodu | Mikro'daki firma kodu | `001` |
| Çalışma Yılı | Sorgulanacak yıl | `2026` |
| Aktif | Bağlantıyı etkinleştir | ✅ |

4. Kaydedin, ardından **Bağlantı Testi** butonunu kullanarak doğrulayın.

---

## Lisans

### Deneme Süresi

Uygulama ilk kurulumdan itibaren **15 gün ücretsiz** olarak çalışır.
Deneme süresi boyunca tüm özellikler kullanılabilir.

Kalan deneme süresi her sayfanın üstünde gösterilir.

### Lisans Satın Alma

Deneme süresi bittikten sonra uygulamayı kullanmaya devam etmek için lisans gereklidir.

1. Lisans için iletişime geçin: **muhasebe_buro@destek.com**
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
