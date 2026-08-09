@echo off
rem ============================================================
rem bat_may.bat - BAT MAY HDH-GIAO (dat console UTF-8 roi chay)
rem   bat_may            -> man hinh dang nhap (an/an hoac goc/goc)
rem   bat_may --goc      -> che do MOT NGUOI DUNG (vao thang quyen goc)
rem   bat_may --luu anh.json      -> khi tat, chup ca he vao anh.json
rem   bat_may --nap anh.json      -> boot lai tu anh da chup
rem   bat_may kich_ban_thu.txt    -> chay kich ban roi thoat
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
python chay_hdh_giao.py %*
endlocal
