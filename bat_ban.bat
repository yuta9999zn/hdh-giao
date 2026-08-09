@echo off
rem ============================================================
rem bat_ban.bat - BAT BAN LAM VIEC (desktop) cua HDH-GIAO
rem   bat_ban              -> mo trinh duyet vao ban lam viec
rem   bat_ban --cong 8099  -> doi cong
rem Dang nhap bang chinh so nguoi dung cua HDH: an/an hoac goc/goc
rem (Muon ban dong-lenh thuan tuy thi chay bat_may.bat)
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
python -u giao_de.py %*
endlocal
