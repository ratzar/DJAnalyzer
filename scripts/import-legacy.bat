@echo off
REM --- Configurazione iniziale: adatta questi percorsi/variabili se cambiano ---
set "PROJECT_PATH=D:\Progetti\DJAnalyzer"
set "BRANCH=import-legacy"
set "COMMIT_MSG=Import legacy code backup in src/"

REM --- Vai nel progetto ---
cd /d "%PROJECT_PATH%"

REM --- Crea o switcha sul branch di import legacy ---
git rev-parse --verify %BRANCH% >nul 2>&1
if errorlevel 1 (
  echo Branch %BRANCH% non esiste, lo creo...
  git checkout -b %BRANCH%
) else (
  echo Passo a branch %BRANCH%...
  git checkout %BRANCH%
)

REM --- Aggiungi, committa e pusha ---
echo Aggiungo tutti i file in src/...
git add src/

echo Creo il commit...
git commit -m "%COMMIT_MSG%"

echo Pusho su origin/%BRANCH%...
git push -u origin %BRANCH%

echo -------------------------------
echo Operazione completata. Premi un tasto per chiudere...
pause >nul