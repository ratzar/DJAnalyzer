@echo off
REM ==========================================
REM Trasferimento_a_GitHub.bat
REM Aggiunge, committa e pusha su GitHub
REM Resta aperto fino a pressione di un tasto
REM ==========================================

REM Salva la cartella corrente e vai nella directory del .bat
pushd "%~dp0"

echo ==========================================
echo      TRASFERIMENTO A GITHUB
echo ==========================================
echo.

REM Chiede all’utente di inserire il messaggio di commit
set /p COMMIT_MSG=Inserisci il messaggio di commit: 

echo.
echo >> ESECUZIONE: git add .
git add .
if errorlevel 1 echo ATTENZIONE: git add ha restituito errore!

echo.
echo >> ESECUZIONE: git commit -m "%COMMIT_MSG%"
git commit -m "%COMMIT_MSG%"
if errorlevel 1 echo ATTENZIONE: git commit ha restituito errore (forse niente da committare)?

echo.
echo >> ESECUZIONE: git push
git push
if errorlevel 1 echo ATTENZIONE: git push ha restituito errore!

echo.
echo ==========================================
echo Operazione completata.
echo Premi un tasto per chiudere...
pause

REM Torna alla cartella precedente
popd
