@echo off
SETLOCAL EnableDelayedExpansion
cls
title Installazione Automatica Ambiente Analisi Video
color 0A

:: 1. VERIFICA VISUAL STUDIO COMPONENTS
echo 🔍 Verifico componenti Visual Studio...
set "vs_components=Microsoft.VisualStudio.Workload.NativeDesktop;Microsoft.VisualStudio.Workload.ManagedDesktopBuildTools;Microsoft.VisualStudio.Component.VC.Tools.x86.x64"

:: Cerca installer VS
where vs_installer.exe >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Installer Visual Studio non trovato
    echo Scaricalo da: https://visualstudio.microsoft.com/it/downloads/
    pause
    exit /b 1
)

:: Installa componenti mancanti
echo ⚙️ Configuro i componenti necessari...
vs_installer.exe modify --installPath "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools" --add %vs_components% --quiet --norestart --wait

:: 2. INSTALLAZIONE PACCHETTI PYTHON
echo 🐍 Configuro Python e pacchetti...
where python >nul || (
    echo ❌ Python non trovato
    winget install -e --id Python.Python.3.10
)

python -m pip install --upgrade pip
python -m pip install opencv-python numpy mediapipe face-recognition dlib torch torchvision torchaudio

:: 3. VERIFICA FINALE
echo ✅ VERIFICA FINALE:
call :check_msbuild
call :check_python
call :check_cmake

pause
exit /b 0

:check_msbuild
where msbuild >nul
if %errorlevel% equ 0 (
    for /f "tokens=2 delims=[]" %%a in ('msbuild /version /nologo') do (
        echo ✔ MSBuild v%%a trovato
    )
) else (
    echo ❌ MSBuild mancante! Riesegui l'installazione
)
exit /b

:check_python
python -c "import cv2, face_recognition; print('✔ Pacchetti Python funzionanti')" || (
    echo ❌ Errore pacchetti Python
    echo Prova: python -m pip install --force-reinstall opencv-python face-recognition
)
exit /b

:check_cmake
where cmake >nul && (
    cmake --version | findstr "version" && echo ✔ CMake configurato
) || (
    echo ❌ CMake mancante
    winget install -e --id Kitware.CMake
)
exit /b