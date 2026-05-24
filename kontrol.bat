@echo off
REM ============================================================
REM  kontrol.bat — Kod Kalitesi & Güvenlik Kontrolü
REM  Kullanım: kontrol.bat
REM  Çalıştır: git commit öncesi veya haftada bir
REM ============================================================
setlocal
cd /d "%~dp0"
set PYTHON=.venv\Scripts\python.exe

echo.
echo ========================================
echo  1/5  RUFF — Linter + Format Kontrolu
echo ========================================
%PYTHON% -m ruff check . --output-format=concise
%PYTHON% -m ruff format --check .

echo.
echo ========================================
echo  2/5  VULTURE — Oldu Kod Tespiti
echo ========================================
%PYTHON% -m vulture sync_motor hesap_yonetimi mikro_sync --min-confidence 80

echo.
echo ========================================
echo  3/5  PIP-AUDIT — Guvenlik Aciklari
echo ========================================
%PYTHON% -m pip_audit -r requirements.txt

echo.
echo ========================================
echo  4/5  BAGIMLILK GUNCELLEME KONTROLU
echo ========================================
%PYTHON% -m pip list --outdated --format=columns

echo.
echo ========================================
echo  5/5  DJANGO SISTEM KONTROLU
echo ========================================
%PYTHON% manage.py check --deploy 2>&1

echo.
echo ========================================
echo  TAMAMLANDI
echo ========================================
pause
