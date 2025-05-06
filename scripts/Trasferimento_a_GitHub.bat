@echo off
setlocal

REM Se non passo “NOEXIT” come argomento, rilancio questo script in un nuovo cmd /k
if "%~1" neq "NOEXIT" (
    start "" cmd /k "%~f0" NOEXIT
    exit /b
)

REM Ora siamo nella finestra che resta aperta
pushd "%~dp0"

echo ==========================================
echo      TRASFERIMENTO A GITHUB
echo ==========================================
echo.

REM Chiede all’utente il messaggio di commit
set /p COMMIT_MSG=Inserisci il messaggio di commit: 
echo.

echo >>> git add .
git add . || echo ERRORE: git add ha restituito errore!

echo.
echo >>> git commit -m "%COMMIT_MSG%"
git commit -m "%COMMIT_MSG%" || echo ERRORE: git commit ha restituito errore (forse niente da committare)

echo.
echo >>> git push
git push || echo ERRORE: git push ha restituito errore!

echo.
echo ==========================================
echo Operazione completata.
echo Premi un tasto per chiudere...
pause

popd
endlocal
