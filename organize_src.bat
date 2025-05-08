@echo off
REM ================================
REM Organize DJAnalyzer: sposta tutti i moduli in src\
REM ================================

REM Assicurati di partire dalla root del progetto
cd /d "%~dp0"

REM Crea src se non esiste
if not exist src (
    mkdir src
)

REM 1) Sposta tutti i .py in root (eccetto questo script) in src\
for %%F in (*.py) do (
    if /I not "%%~nxF"=="organize_src.bat" (
        echo Sposto %%F in src\
        move "%%F" "src\"
    )
)

REM 2) Sposta tutti i .py da scripts\ in src\
if exist scripts (
    for %%F in (scripts\*.py) do (
        echo Sposto scripts\%%~nxF in src\
        move "scripts\%%~nxF" "src\"
    )
)

REM 3) Elimina la cartella scripts se vuota
rd /s /q scripts

echo.
echo Tutti i moduli Python sono stati spostati in src\
pause

