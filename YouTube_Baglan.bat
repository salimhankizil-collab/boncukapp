@echo off
chcp 65001 >nul
cd /d "%~dp0uretim"
echo.
echo  YouTube baglantisi kuruluyor...
echo  Tarayicida Google izin sayfasi acilacak: hesabini sec ve "Izin ver" de.
echo  ("Google bu uygulamayi dogrulamadi" uyarisi cikarsa: Gelismis - Boncuk Otomasyon'a git)
echo.
if exist "..\gizli\token.json" del "..\gizli\token.json"
python baglan.py
echo.
pause
