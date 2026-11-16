@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo  Bilgisayardaki proje GitHub ile esitleniyor...
echo.
git pull --rebase --autostash origin main
if errorlevel 1 ( echo HATA: GitHub'dan cekilemedi. & pause & exit /b 1 )
echo.
echo  Buluttaki yeni bolum videolari indiriliyor (bilgisayarda olanlar atlanir)...
python uretim\videolari_indir.py
echo.
echo  Tamam! Kod GitHub ile ayni, yeni videolar "videolar" klasorunde kendi bolum klasorlerinde.
pause
