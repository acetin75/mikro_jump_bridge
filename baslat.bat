@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
title Muhasebe Bürosu CRM

echo ============================================================
echo   Muhasebe Bürosu CRM - Kurulum ve Başlatma
echo ============================================================
echo.

cd /d "%~dp0"

:: Sanal ortam kontrolü
if not exist ".venv\Scripts\activate.bat" (
    echo [1/4] Sanal ortam oluşturuluyor...
    python -m venv .venv
    if errorlevel 1 (
        echo.
        echo HATA: Python bulunamadı veya venv oluşturulamadı.
        echo Python 3.10+ kurulu ve PATH tanımlı olduğundan emin olun.
        echo https://python.org adresinden indirin.
        echo.
        pause
        exit /b 1
    )
)

:: Aktive et
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo HATA: Sanal ortam aktive edilemedi.
    pause
    exit /b 1
)

:: Paket kurulumu
echo [2/4] Gerekli paketler kontrol ediliyor...
pip install -r requirements.txt -q
if errorlevel 1 (
    echo.
    echo HATA: Paket kurulumu başarısız. İnternet bağlantınızı kontrol edin.
    echo.
    pause
    exit /b 1
)

:: Migration
echo [3/4] Veritabanı hazırlanıyor...
python manage.py migrate --run-syncdb
if errorlevel 1 (
    echo.
    echo HATA: Veritabanı migrate işlemi başarısız.
    echo.
    pause
    exit /b 1
)

:: Superuser oluştur (yoksa)
python olustur_admin.py
if errorlevel 1 (
    echo UYARI: Admin hesabı oluşturulamadı, devam ediliyor...
)

:: 8000 portunu kullanan varsa sonlandır
echo Port 8000 kontrol ediliyor...
for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr ":8000 " ^| findstr "LISTENING"') do (
    echo Port 8000 kullanımda ^(PID: %%a^), kapatılıyor...
    taskkill /PID %%a /F >nul 2>&1
)

:: Port seçimi — 8000 hâlâ doluysa 8001, 8002 dene
set PORT=8000
for %%p in (8000 8001 8002 8003) do (
    if "!PORT_BULUNDU!" == "" (
        netstat -aon 2>nul | findstr ":%%p " | findstr "LISTENING" >nul 2>&1
        if errorlevel 1 (
            set PORT=%%p
            set PORT_BULUNDU=1
        )
    )
)

:: Başlat
echo [4/4] Sunucu başlatılıyor...
echo.
echo ============================================================
echo   Uygulama: http://127.0.0.1:%PORT%
echo   Admin:    http://127.0.0.1:%PORT%/admin
echo   Kullanici: admin  /  Sifre: admin123
echo   Durdurmak için: Ctrl+C
echo ============================================================
echo.

:: Sunucu hazırlanırken tarayıcıyı 2 saniye sonra otomatik aç
start /b cmd /c "timeout /t 2 /nobreak >nul && start http://127.0.0.1:%PORT%"

python manage.py runserver 127.0.0.1:%PORT%

echo.
echo Sunucu durdu.
pause
