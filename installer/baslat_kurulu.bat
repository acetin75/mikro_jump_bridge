@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
title Mikro Jump Bridge
cd /d "%~dp0"

set "PYTHON=%~dp0python_dist\python.exe"

echo.
echo  ===================================================
echo   Mikro Jump Bridge  (Port: 8001)
echo  ===================================================
echo.

:: Python kontrolü
if not exist "%PYTHON%" (
    echo HATA: python_dist\python.exe bulunamadı.
    echo Kurulum bozuk olabilir. Lütfen yeniden kurun.
    pause
    exit /b 1
)

:: .env yoksa varsayılanı oluştur
if not exist ".env" (
    if exist ".env.example" (
        copy ".env.example" ".env" >nul
        echo  [Kurulum] .env dosyası oluşturuldu.
    )
)

:: Migration
echo  [1/3] Veritabanı güncelleniyor...
"%PYTHON%" manage.py migrate --run-syncdb >nul 2>&1

:: Admin hesabı
echo  [2/3] Admin hesabı kontrol ediliyor...
"%PYTHON%" olustur_admin.py >nul 2>&1

echo.
echo  Sunucu başlatılıyor: http://127.0.0.1:8001
echo  Durdurmak için: Ctrl+C
echo.

start "" http://127.0.0.1:8001
"%PYTHON%" manage.py runserver 8001
