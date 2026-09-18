@echo off
rem Suflor - cift tikla ac (konsol penceresi acilmaz). Dil, kisayol ve sozluk uygulama ayarlarindadir.
cd /d "%~dp0"
if exist "%~dp0.venv\Scripts\pythonw.exe" (
    start "" "%~dp0.venv\Scripts\pythonw.exe" "%~dp0demo\kabuk.py" %*
    exit /b 0
)

where pythonw.exe >nul 2>nul
if not errorlevel 1 (
    start "" pythonw.exe "%~dp0demo\kabuk.py" %*
    exit /b 0
)

powershell.exe -NoProfile -WindowStyle Hidden -Command "Add-Type -AssemblyName PresentationFramework; [System.Windows.MessageBox]::Show('Suflor icin Python bulunamadi. Kurulum adimlarini yeniden calistir.', 'Suflor')" >nul 2>nul
exit /b 1
