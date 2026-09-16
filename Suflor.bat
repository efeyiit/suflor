@echo off
rem Suflör — çift tıkla aç (konsol penceresi açılmaz). Dil/kısayol/sözlük: uygulamadaki ⚙ düğmesi.
cd /d "%~dp0"
start "" pythonw demo\kabuk.py %*
