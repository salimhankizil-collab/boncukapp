@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo  Bilgisayardaki proje GitHub ile esitleniyor...
echo.
git pull --rebase --autostash origin main
if errorlevel 1 ( echo HATA: GitHub'dan cekilemedi. & pause & exit /b 1 )
echo.
echo  Buluttaki bolum videolari indiriliyor (zaten olanlar atlanir)...
for /f "delims=" %%r in ('gh release list --repo salimhankizil-collab/boncukapp --limit 100 --json tagName -q ".[].tagName"') do (
  gh release download %%r --repo salimhankizil-collab/boncukapp --dir "videolar\%%r" --skip-existing
)
echo.
echo  Tamam! Kod GitHub ile ayni, yeni videolar "videolar" klasorunde.
pause
