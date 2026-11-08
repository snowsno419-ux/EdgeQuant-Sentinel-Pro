@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title EdgeQuant - Windows Installer Diagnostics
if not exist "%~dp0EDGEQUANT-INSTALLER-DIAGNOSIS.ps1" (
  echo [ERROR] Missing EDGEQUANT-INSTALLER-DIAGNOSIS.ps1
  pause
  exit /b 3
)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0EDGEQUANT-INSTALLER-DIAGNOSIS.ps1"
set "RESULT=%ERRORLEVEL%"
echo.
echo Diagnostic report: "%~dp0EDGEQUANT-INSTALLER-DIAGNOSIS.txt"
echo If installer failed, also look at: "%~dp0CLIENT-INSTALLER-BUILD.log"
echo Share only the last error lines. Remove any passwords, API keys or session details.
echo.
pause
exit /b %RESULT%
