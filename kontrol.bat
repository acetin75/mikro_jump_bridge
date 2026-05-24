@echo off
REM ============================================================
REM  kontrol.bat - Kod Kalitesi ve Guvenlik Kontrolu (fail-fast)
REM  Kullanim: kontrol.bat
REM  Calistir: git commit oncesi veya haftada bir
REM
REM  Her adim hata verirse betik 1 ile cikar; sonda "BASARILI"
REM  yalnizca tum adimlar gectiyse yazilir.
REM ============================================================
setlocal
cd /d "%~dp0"
set PYTHON=.venv\Scripts\python.exe

echo.
echo ========================================
echo  1/6  RUFF - Linter
echo ========================================
%PYTHON% -m ruff check . --output-format=concise
if errorlevel 1 goto :hata

echo.
echo ========================================
echo  2/6  RUFF - Format kontrolu
echo ========================================
%PYTHON% -m ruff format --check .
if errorlevel 1 goto :hata

echo.
echo ========================================
echo  3/6  VULTURE - Olu kod tespiti
echo ========================================
%PYTHON% -m vulture sync_motor hesap_yonetimi lisans posta kullanici mikro_sync --min-confidence 80
if errorlevel 1 goto :hata

echo.
echo ========================================
echo  4/6  PIP-AUDIT - Guvenlik aciklari
echo ========================================
%PYTHON% -m pip_audit -r requirements.txt
if errorlevel 1 goto :hata

echo.
echo ========================================
echo  5/6  DJANGO sistem kontrolu
echo ========================================
%PYTHON% manage.py check
if errorlevel 1 goto :hata

echo.
echo ========================================
echo  6/6  TESTLER
echo ========================================
%PYTHON% manage.py test --verbosity=1
if errorlevel 1 goto :hata

echo.
echo ========================================
echo  BASARILI - Tum kalite kapilari gecti
echo ========================================
echo.
echo (Bilgi) Eski paketleri gormek icin:
echo   %PYTHON% -m pip list --outdated
echo.
pause
exit /b 0

:hata
echo.
echo ========================================
echo  HATA - Yukaridaki adimda kalite kapisi
echo  basarisiz oldu. Commit ETMEYIN.
echo ========================================
pause
exit /b 1
