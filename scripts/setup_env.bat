@echo off
echo ===== Creazione ambiente virtuale =====
python -m venv venv

echo.
echo ===== Attivazione ambiente virtuale =====
call venv\Scripts\activate

echo.
echo ===== Installazione dipendenze =====
pip install --upgrade pip
pip install librosa matplotlib pandas pillow

echo.
echo Ambiente configurato con successo.
pause
