@echo off
rem ============================================================
rem bat_xa.bat - MO CONG DANG NHAP TU XA cua HDH-GIAO
rem   bat_xa               -> nghe 127.0.0.1:2222
rem   bat_xa --cong 2300   -> doi cong
rem Roi tu cua so khac:  python khach_xa.py --cong 2222
rem CANH BAO: KHONG ma hoa duong truyen. Chi nghe 127.0.0.1 (cung mot may).
rem ============================================================
setlocal
cd /d "%~dp0"
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
where python >nul 2>nul
if errorlevel 1 (
  echo [loi] Khong tim thay 'python' tren PATH. Cai Python 3.11+ roi thu lai.
  exit /b 1
)
python -u chay_hdh_xa.py %*
endlocal
