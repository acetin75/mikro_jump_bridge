@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
title Mikro Sync — ERP Köprüsü
cd /d "%~dp0"

echo.
echo  ===================================================
echo   Mikro Sync — Mikro ERP Köprüsü  (Port: 8001)
echo  ===================================================
echo.

:: Sanal ortam kontrolü / oluşturma
if not exist ".venv\Scripts\python.exe" (
    echo [1/4] Sanal ortam oluşturuluyor...
    python -m venv .venv
    if errorlevel 1 (
        echo.
        echo HATA: Python bulunamadı veya venv oluşturulamadı.
        echo Python 3.10+ kurulu ve PATH tanımlı olduğundan emin olun.
        pause
        exit /b 1
    )
)

:: Paket kurulumu
echo [2/4] Gerekli paketler kontrol ediliyor...
.venv\Scripts\python.exe -m pip install -r requirements.txt -q
if errorlevel 1 (
    echo.
    echo HATA: Paket kurulumu başarısız. İnternet bağlantınızı kontrol edin.
    pause
    exit /b 1
)

:: Migration
echo [3/4] Veritabanı hazırlanıyor...
.venv\Scripts\python.exe manage.py migrate --run-syncdb
if errorlevel 1 (
    echo.
    echo HATA: Veritabanı migrate işlemi başarısız.
    pause
    exit /b 1
)

:: Admin kullanıcısı oluştur (yoksa)
echo [4/4] Admin hesabı kontrol ediliyor...
.venv\Scripts\python.exe olustur_admin.py
if errorlevel 1 (
    echo UYARI: Admin hesabı oluşturulamadı, devam ediliyor...
)

:: -------------------------------------------------------
:: Cloudflare Tunnel (isteğe bağlı — .env'de TUNNEL_TOKEN varsa başlatır)
:: -------------------------------------------------------
set "CF_TUNNEL_TOKEN="
set "CF_TUNNEL_HOST="
if exist ".env" (
    for /f "usebackq tokens=1* delims==" %%a in (".env") do (
        if "%%a"=="TUNNEL_TOKEN"    set "CF_TUNNEL_TOKEN=%%b"
        if "%%a"=="TUNNEL_HOSTNAME" set "CF_TUNNEL_HOST=%%b"
    )
)
if defined CF_TUNNEL_TOKEN (
    where cloudflared >nul 2>&1
    if not errorlevel 1 (
        echo  Cloudflare Tunnel başlatılıyor: !CF_TUNNEL_HOST!
        start /b cloudflared tunnel --no-autoupdate run --token !CF_TUNNEL_TOKEN!
    ) else if exist "cloudflared.exe" (
        echo  Cloudflare Tunnel başlatılıyor: !CF_TUNNEL_HOST!
        start /b "cloudflared" cloudflared.exe tunnel --no-autoupdate run --token !CF_TUNNEL_TOKEN!
    ) else (
        echo  [UYARI] TUNNEL_TOKEN .env'de tanımlı ama cloudflared bulunamadı.
        echo          cloudflared.exe'yi proje klasörüne koyun ya da PATH'e ekleyin.
        echo          İndirme: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
    )
)

echo.
echo  Sunucu başlatılıyor: http://127.0.0.1:8001
if defined CF_TUNNEL_HOST echo  Dış erişim:  https://!CF_TUNNEL_HOST!
echo  Durdurmak için: Ctrl+C
echo.

start "" http://127.0.0.1:8001

.venv\Scripts\python.exe manage.py runserver 8001

pause
