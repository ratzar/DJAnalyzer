@echo off
title Avvio DJPRO - Analisi Audio
echo Avvio DJPRO...
python DJpro.py 2> djpro_error.log

echo.
echo Se ci sono errori, sono stati salvati in djpro_error.log
pause
