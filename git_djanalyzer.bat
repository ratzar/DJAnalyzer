@echo off
cd /d D:\progetti\DJAnalyzer
git add .
set /p msg="Inserisci il messaggio del commit: "
git commit -m "%msg%"
for /f %%i in ('git rev-parse --abbrev-ref HEAD') do set curr_branch=%%i
git push -u origin %curr_branch%
pause
