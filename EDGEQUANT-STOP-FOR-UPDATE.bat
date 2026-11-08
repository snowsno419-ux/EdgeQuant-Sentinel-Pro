@echo off
setlocal
cd /d "%~dp0"
echo.
echo EdgeQuant - stop app before update [does not delete data]
echo Close the trading engine safely before proceeding.
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0EDGEQUANT-STOP-FOR-UPDATE.ps1"
echo.
pause
