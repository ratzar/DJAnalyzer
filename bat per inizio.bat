@echo off

git add .
set /p msg="Inserisci il messaggio del commit: "
git commit -m "%msg%"
git push origin main
pause
