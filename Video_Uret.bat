@echo off
chcp 65001 >nul
cd /d "%~dp0uretim"
echo.
echo  Boncuk video fabrikasi
echo  ----------------------
set /p ADET="Kac video uretilsin? (bir hafta icin 7 yaz, Enter = 1): "
if "%ADET%"=="" set ADET=1
python uret.py --adet %ADET%
echo.
echo  Bitti! Videolar "videolar" klasorunde.
start "" "%~dp0videolar"
pause
