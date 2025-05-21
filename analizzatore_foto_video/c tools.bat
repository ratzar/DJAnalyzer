@echo off
SETLOCAL

:: Configurazione cartelle
SET "ROOT_DIR=%~dp0"
SET "ENV_DIR=%ROOT_DIR%env_analizzatore"
SET "SCRIPT_NAME=analizzatore_foto_video.py"

title Analizzatore Video/Foto - In esecuzione...

:: Controlla se CMake è installato
where cmake >nul 2>&1
if errorlevel 1 (
    echo ERRORE: CMake non è installato o non è nel PATH.
    echo Scaricalo da https://cmake.org/download e aggiungilo al PATH.
    pause
    exit /b 1
)

:: Crea/attiva ambiente virtuale
if not exist "%ENV_DIR%" (
    echo Creazione ambiente virtuale...
    python -m venv "%ENV_DIR%"
    if errorlevel 1 (
        echo ERRORE: Creazione ambiente fallita.
        pause
        exit /b 1
    )
)

call "%ENV_DIR%\Scripts\activate.bat"

:: Installa pacchetti (con flag --no-build-isolation per dlib)
echo Installazione dipendenze...
pip install --upgrade pip setuptools wheel
pip install cmake  # Necessario per compilare dlib
pip install opencv-python numpy mediapipe scikit-learn torch torchvision pillow
pip install face-recognition --no-build-isolation  # Fix per dlib

if errorlevel 1 (
    echo ERRORE: Installazione fallita. Controlla che CMake e Visual C++ Build Tools siano installati.
    pause
    exit /b 1
)

:: Esegui lo script
echo Avvio analisi...
python "%SCRIPT_NAME%"

if errorlevel 1 (
    echo ERRORE durante l'esecuzione.
) else (
    echo Analisi completata!
)

pause