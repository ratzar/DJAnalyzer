@echo off
SETLOCAL EnableDelayedExpansion
color 0A
title Controllo Ambiente di Sviluppo

echo.
echo ###################################################
echo #           VERIFICA COMPONENTI INSTALLATI        #
echo ###################################################
echo.

:: 1. Controllo Visual Studio 2022 e Build Tools
echo === VERIFICA VISUAL STUDIO 2022 (17.13.6) ===
where msbuild >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=2* delims=[]" %%a in ('msbuild /version /nologo') do (
        set "msbuild_ver=%%a"
    )
    echo [SUCCESS] MSBuild trovato (Versione: !msbuild_ver!)
) else (
    echo [ERROR] MSBuild non trovato! Installa "Desktop development with C++"
)

where cl >nul 2>&1
if %errorlevel% equ 0 (
    for /f "delims=[] tokens=2" %%a in ('cl /? ^| findstr /C:"Version"') do (
        set "cl_ver=%%a"
    )
    echo [SUCCESS] Compilatore C++ trovato (Versione: !cl_ver!)
) else (
    echo [ERROR] Compilatore C++ mancante! Installa "MSVC v143"
)

:: 2. Controllo Windows SDK
echo.
echo === VERIFICA WINDOWS SDK ===
reg query "HKLM\SOFTWARE\Microsoft\Windows Kits\Installed Roots" /v KitsRoot10 >nul 2>&1
if %errorlevel% equ 0 (
    echo [SUCCESS] Windows 10/11 SDK installato
) else (
    echo [ERROR] Windows SDK mancante! Installa "Windows 11 SDK (10.0.22621.0)"
)

:: 3. Controllo CMake
echo.
echo === VERIFICA CMAKE ===
where cmake >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=3" %%a in ('cmake --version ^| findstr /C:"cmake version"') do (
        set "cmake_ver=%%a"
    )
    echo [SUCCESS] CMake trovato (Versione: !cmake_ver!)
) else (
    echo [ERROR] CMake non installato! Scaricalo da cmake.org
)

:: 4. Controllo Python e pacchetti
echo.
echo === VERIFICA PYTHON E PACCHETTI ===
where python >nul 2>&1
if %errorlevel% equ 0 (
    python --version >nul 2>&1
    if %errorlevel% equ 0 (
        for /f "tokens=2" %%a in ('python --version') do (
            set "python_ver=%%a"
        )
        echo [SUCCESS] Python trovato (Versione: !python_ver!)

        echo.
        echo === PACCHETTI PYTHON NECESSARI ===
        pip list --format=freeze > packages.txt
        findstr /i "opencv-python numpy mediapipe face-recognition torch torchvision pillow" packages.txt
        if %errorlevel% equ 0 (
            echo [SUCCESS] Tutti i pacchetti Python sono installati
        ) else (
            echo [ERROR] Alcuni pacchetti mancano! Esegui:
            echo pip install opencv-python numpy mediapipe face-recognition torch torchvision pillow
        )
        del packages.txt
    )
) else (
    echo [ERROR] Python non trovato! Installa Python 3.10
)

:: 5. Controllo ambiente virtuale (se esiste)
echo.
echo === VERIFICA AMBIENTE VIRTUALE ===
if exist "D:\aitools\env_analizzatore\Scripts\activate.bat" (
    echo [SUCCESS] Ambiente virtuale trovato in D:\aitools\env_analizzatore
) else (
    echo [WARNING] Nessun ambiente virtuale trovato. Consigliato crearlo con:
    echo python -m venv D:\aitools\env_analizzatore
)

echo.
echo ###################################################
echo #           RIEPILOGO ERRORI                     #
echo ###################################################
echo.
findstr /i "ERROR" %0
if %errorlevel% equ 1 (
    echo ✅ Tutti i controlli sono passati con successo!
) else (
    echo ❌ Alcuni componenti mancano. Correggi gli errori sopra.
)

echo.
pause