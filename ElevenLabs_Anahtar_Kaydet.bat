@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist gizli mkdir gizli
echo.
echo  ElevenLabs API anahtarini yapistir ve Enter'a bas.
echo  (Yazdigin ekranda gorunmez. Anahtar sadece bu bilgisayardaki "gizli" klasorune kaydedilir, GitHub'a gitmez.)
echo.
powershell -NoProfile -Command "$s = Read-Host -AsSecureString 'Anahtar'; $b = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($s); $k = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($b); [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($b); if ($k.Trim().Length -lt 20) { Write-Host 'HATA: anahtar cok kisa, tekrar dene.'; exit 1 }; [IO.File]::WriteAllText('gizli\elevenlabs_key.txt', $k.Trim()); Write-Host 'Kaydedildi.'"
echo.
pause
