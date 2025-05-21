@echo off
SETLOCAL

:: Configurazione cartelle
SET "ROOT_DIR=%~dp0"
SET "ENV_DIR=%ROOT_DIR%env_analizzatore"
SET "SCRIPT_NAME=analizzatore_foto_video.py"

title Analizzatore Video/Foto - In esecuzione...

:: Controlla se l'ambiente esiste già
if not exist "%ENV_DIR%" (
    echo Creazione ambiente virtuale...
    python -m venv "%ENV_DIR%"
    if errorlevel 1 (
        echo ERRORE: Creazione ambiente fallita. Controlla che Python sia installato.
        pause
        exit /b 1
    )
)

:: Attiva l'ambiente
echo Attivazione ambiente virtuale...
call "%ENV_DIR%\Scripts\activate"

:: Installa pacchetti
echo Installazione dipendenze...
pip install --upgrade pip setuptools wheel
pip install opencv-python numpy mediapipe face-recognition scikit-learn torch torchvision pillow

if errorlevel 1 (
    echo ERRORE: Installazione pacchetti fallita.
    pause
    exit /b 1
)

:: Esegui lo script
echo Avvio analisi...
python "%SCRIPT_NAME%"

if errorlevel 1 (
    echo ERRORE: Esecuzione script fallita.
) else (
    echo Analisi completata con successo!
)

:: Mantiene la finestra aperta
echo.
echo Premere un tasto per uscire...
pause >nul