@echo off
SETLOCAL EnableDelayedExpansion
cls
title CONTROLLO COMPLETO AMBIENTE
color 0A

echo ╔════════════════════════════════════╗
echo ║    VERIFICA DEFINITIVA AMBIENTE    ║
echo ╚════════════════════════════════════╝

echo 🔍 [1/4] VERIFICO VISUAL STUDIO...
where msbuild >nul
if %errorlevel% equ 0 (
    for /f "tokens=2 delims=[]" %%a in ('msbuild /version /nologo') do (
        echo ✔ MSBuild v%%a TROVATO
        set "msbuild_ok=1"
    )
) else (
    echo ❌ MSBuild NON TROVATO - Installa "Desktop development with C++"
)

where cl >nul
if %errorlevel% equ 0 (
    cl 2>&1 | findstr "Version" >nul && (
        echo ✔ Compilatore C++ TROVATO
        set "cl_ok=1"
    )
) else (
    echo ❌ Compilatore C++ MANCANTE
)

echo 🔍 [2/4] VERIFICO PYTHON...
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✔ Python !python_version! TROVATO
    python -c "import sys; print(f'    Path: {sys.executable}')"
    
    echo 🔍 Pacchetti Python:
    python -c "try: import cv2, face_recognition, torch; print('✔ OpenCV, face-recognition e PyTorch OK'); exit(0) except ImportError as e: print(f'❌ Errore: {e}'); exit(1)"
) else (
    echo ❌ Python NON TROVATO
)

echo 🔍 [3/4] VERIFICO CMAKE...
where cmake >nul
if %errorlevel% equ 0 (
    for /f "tokens=3" %%a in ('cmake --version') do (
        echo ✔ CMake v%%a TROVATO
        set "cmake_ok=1"
    )
) else (
    echo ❌ CMake NON TROVATO
)

echo 🔍 [4/4] VERIFICA VIDEO TEST...
if exist "test_video.py" (
    python test_video.py
) else (
    echo ⚠️ Crea test_video.py per verificare l'analisi video
)

echo ╔════════════════════════════════════╗
echo ║          RISULTATO FINALE          ║
echo ╠════════════════════════════════════╣
if defined msbuild_ok if defined cl_ok if defined cmake_ok (
    echo ║  ✅  AMBIENTE CONFIGURATO CORRETTAMENTE  ║
) else (
    echo ║  ❌  PROBLEMI RILEVATI - VEDI SOPRA  ║
)
echo ╚════════════════════════════════════╝

pause