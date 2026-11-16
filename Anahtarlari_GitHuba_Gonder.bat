@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo  Google anahtarlari GitHub'a (gizli olarak) gonderiliyor...
echo  Bu dosyalarin icerigi ekranda gosterilmez, sadece GitHub'in sifreli "Secrets" bolumune gider.
echo.
if not exist "gizli\client_secret.json" ( echo HATA: gizli\client_secret.json yok. & pause & exit /b 1 )
if not exist "gizli\token.json" ( echo HATA: gizli\token.json yok. Once YouTube_Baglan.bat calistir. & pause & exit /b 1 )
gh secret set GOOGLE_CLIENT_SECRET --repo salimhankizil-collab/boncukapp < "gizli\client_secret.json"
gh secret set GOOGLE_TOKEN --repo salimhankizil-collab/boncukapp < "gizli\token.json"
echo.
echo  Tamam! Bulut artik YouTube'a baglanabilir.
pause
