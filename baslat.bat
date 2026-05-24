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

:: Statik dosyalar
echo [4/5] Statik dosyalar hazırlanıyor...
.venv\Scripts\python.exe manage.py collectstatic --noinput -v 0
if errorlevel 1 (
    echo UYARI: collectstatic başarısız oldu, devam ediliyor...
)

:: Admin kullanıcısı oluştur (yoksa)
echo [5/5] Admin hesabı kontrol ediliyor...
.venv\Scripts\python.exe olustur_admin.py
if errorlevel 1 (
    echo UYARI: Admin hesabı oluşturulamadı, devam ediliyor...
)

echo.
echo  Sunucu başlatılıyor: http://127.0.0.1:8001
echo  Durdurmak için: Ctrl+C
echo.

start "" http://127.0.0.1:8001

.venv\Scripts\python.exe manage.py runserver 8001

pause
