@echo off
REM Naviga alla cartella del progetto
cd /d "%~dp0"

REM Controlla lo status e aggiunge tutte le modifiche
git status
git add .

REM Commit con messaggio predefinito
git commit -m "Aggiornamenti interfaccia e cue" >nul 2>&1

REM Push sul branch corrente
git push >nul 2>&1

echo Operazione GitHub completata con messaggio fisso.
pause
