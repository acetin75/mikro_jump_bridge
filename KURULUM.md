# Muhasebe Bürosu CRM — Windows Kurulum Rehberi

Bu rehber, bilgisayarınıza **hiç Python kurulmamış** olsa bile uygulamayı
sıfırdan çalışır hale getirmenizi sağlar.

---

## Adım 1 — Python Kurun

> Python 3.10 veya daha yeni bir sürüm gereklidir.

1. https://python.org/downloads adresini açın.
2. **"Download Python 3.x.x"** düğmesine tıklayın.
3. İndirilen `.exe` dosyasını çalıştırın.
4. Kurulum ekranında **"Add Python to PATH"** onay kutusunu işaretleyin.
5. **"Install Now"** düğmesine tıklayın ve kurulum tamamlanana kadar bekleyin.

Kurulumu doğrulamak için:
- `Windows + R` → `cmd` yazıp Enter.
- Açılan pencerede şunu yazın ve Enter'a basın:

```cmd
python --version
```

`Python 3.x.x` gibi bir çıktı görüyorsanız kurulum başarılı.

---

## Adım 2 — Uygulamayı İndirin

### Seçenek A — ZIP olarak indir (önerilen, Git bilgisi gerekmez)

1. https://github.com/acetin75/muhasebe-buro-crm adresini açın.
2. Yeşil **"Code"** düğmesine tıklayın → **"Download ZIP"** seçin.
3. İndirilen `muhasebe-buro-crm-main.zip` dosyasını sağ tıklayıp
   **"Tümünü Çıkar..."** ile `C:\muhasebe_buro\` klasörüne çıkarın.

### Seçenek B — Git ile klonla

```cmd
git clone https://github.com/acetin75/muhasebe-buro-crm.git C:\muhasebe_buro
```

---

## Adım 3 — Ortam Dosyasını Oluşturun

Uygulama, hassas ayarlar için `.env` dosyası kullanır.

1. `C:\muhasebe_buro\` klasörünü Dosya Gezgini'nde açın.
2. `.env.example` dosyasını kopyalayıp `.env` olarak yeniden adlandırın.
3. `.env` dosyasını Not Defteri ile açın ve bilgileri doldurun:

```ini
SECRET_KEY=buraya-rastgele-uzun-bir-sifre-yazin
DEBUG=True

# E-posta ayarları (isteğe bağlı, hatırlatmalar için)
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=

# Hatırlatma alıcısı (isteğe bağlı)
HATIRLATMA_ALICI=

# Firma bilgileri (e-fatura XML için)
FIRMA_ADI=Şirket Adı A.Ş.
FIRMA_VKN=1234567890
FIRMA_VERGI_DAIRESI=Kadıköy
FIRMA_ADRES=İstanbul, Türkiye
```

> **SECRET_KEY ipucu:** Rastgele güvenli bir anahtar için şunu kullanabilirsiniz:
> `python -c "import secrets; print(secrets.token_urlsafe(50))"`

---

## Adım 4 — Uygulamayı Başlatın

`C:\muhasebe_buro\` klasörüne gidin ve `baslat.bat` dosyasına **çift tıklayın**.

İlk çalışmada otomatik olarak:
1. Sanal Python ortamı oluşturulur (`.venv/` klasörü).
2. Gerekli tüm paketler kurulur (~2-5 dakika, internet bağlantısı gerekir).
3. Veritabanı tabloları hazırlanır.
4. Yönetici hesabı oluşturulur (`admin` / `admin123`).
5. Tarayıcı otomatik açılır.

Bir siyah terminal penceresi açılacak ve şuna benzer bir çıktı göreceksiniz:

```
============================================================
  Uygulama: http://127.0.0.1:8000
  Admin:    http://127.0.0.1:8000/admin
  Kullanici: admin  /  Sifre: admin123
  Durdurmak için: Ctrl+C
============================================================
```

Tarayıcı otomatik açılmazsa http://127.0.0.1:8000 adresini manuel açın.

---

## Adım 5 — İlk Giriş ve Şifre Değiştirme

1. Tarayıcıda http://127.0.0.1:8000 adresini açın.
2. Kullanıcı adı: `admin` — Şifre: `admin123` ile giriş yapın.
3. Sağ üst menüden **Şifremi Değiştir** seçeneğiyle şifrenizi güncelleyin.
4. **Kullanıcılar** menüsünden (Yönetici rolü gerekir) ek kullanıcı ekleyebilirsiniz.

---

## Adım 6 — Her Günkü Kullanım

- Uygulamayı başlatmak için her seferinde `baslat.bat`'a çift tıklayın.
- Terminal penceresini kapatmak veya `Ctrl+C` yapmak uygulamayı durdurur.
- Bilgisayarı kapattığınızda uygulama otomatik durur; açtığınızda tekrar `baslat.bat` çalıştırın.

---

## Veri Yedekleme

Tüm veriler `C:\muhasebe_buro\db.sqlite3` dosyasındadır.

**Yedek almak için** bu dosyayı kopyalayın:

```cmd
copy C:\muhasebe_buro\db.sqlite3 C:\muhasebe_buro\db_yedek_%date:~6,4%%date:~3,2%%date:~0,2%.sqlite3
```

Veya uygulamanın **Dashboard** sayfasındaki **"Yedeği İndir"** düğmesini kullanın.

---

## Sık Sorulan Sorular

### "python bulunamadı" hatası alıyorum

Python kurulurken "Add Python to PATH" seçeneği işaretlenmemiş olabilir.
Çözüm: Python'u kaldırıp yeniden kurun ve kurulum sırasında PATH seçeneğini işaretleyin.

### Tarayıcı açılmıyor / http://127.0.0.1:8000 çalışmıyor

Terminal penceresinin açık olduğundan emin olun. Terminal kapanmışsa `baslat.bat`'a tekrar çift tıklayın.

### "Port zaten kullanımda" mesajı alıyorum

`baslat.bat` otomatik olarak 8000 portunu kullanan uygulamayı kapatmaya çalışır.
Sorun devam ederse bilgisayarı yeniden başlatın.

### Şifremi unuttum

Terminal penceresinde (`.venv` aktifken) şunu çalıştırın:

```cmd
python manage.py changepassword admin
```

### Uygulama nasıl güncellenir?

1. Yeni sürümü GitHub'dan ZIP olarak indirin.
2. `db.sqlite3` dosyanızı yedekleyin.
3. Yeni dosyaları üzerine yazın (`db.sqlite3` dosyanıza dokunmayın).
4. `baslat.bat`'ı çalıştırın — migration'lar otomatik uygulanır.

---

## Teknik Destek

- GitHub Issues: https://github.com/acetin75/muhasebe-buro-crm/issues
- Yeni sürümler: https://github.com/acetin75/muhasebe-buro-crm/releases
