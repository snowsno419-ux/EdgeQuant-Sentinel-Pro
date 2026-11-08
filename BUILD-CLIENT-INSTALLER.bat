@echo off
setlocal EnableExtensions DisableDelayedExpansion
title EdgeQuant Sentinel - CLIENT INSTALLER (KEEP OPEN + ERROR LOG)
cd /d "%~dp0"
if errorlevel 1 (
  echo [ERROR] Cannot access the installer source directory.
  echo Extract the entire ZIP to a short, writable local folder on Windows.
  pause
  exit /b 80
)
set "BUILD_LOG=%~dp0CLIENT-INSTALLER-BUILD.log"
echo.
echo ================================================================
echo       EDGEQUANT - CLIENT INSTALLER BUILD WITH DIAGNOSTICS
echo ================================================================
echo.
echo The build may stop if Python, Inno Setup, source files, or tests fail.
echo Every error will remain visible and be saved to the build log.
echo DO NOT distribute a partial dist folder after a failure.
echo.
echo LOG: "%BUILD_LOG%"
echo.
where powershell.exe >nul 2>nul
if errorlevel 1 goto no_powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0RUN-CLIENT-INSTALLER-LOGGED.ps1" -BuildScript "%~dp0BUILD-CLIENT-INSTALLER-CORE.bat" -LogFile "%BUILD_LOG%"
set "BUILD_RESULT=%ERRORLEVEL%"
goto end_build
:no_powershell
echo [ERROR] Windows PowerShell could not be found.
echo [INFO] Run the core builder with "cmd /k BUILD-CLIENT-INSTALLER-CORE.bat" for details.
set "BUILD_RESULT=81"
:end_build
echo.
echo ================================================================
if "%BUILD_RESULT%"=="0" (
  echo [SUCCESS] Client Setup.exe was built. Test on a clean DEMO PC.
  echo Output: "%~dp0dist\EdgeQuant-Sentinel-Client-Setup.exe"
) else (
  echo [FAILED] Build exited with code %BUILD_RESULT%.
  echo [FAILED] Read the LAST ERROR above or the full log:
  echo          "%BUILD_LOG%"
  echo [FAILED] Do not send an unfinished dist folder to clients.
)
echo ================================================================
echo.
echo This CMD window will STAY OPEN until you press a key.
echo If this window STILL closes, open Command Prompt, cd to the extracted
echo folder and run BUILD-CLIENT-INSTALLER.bat manually to see the error.
echo.
pause
exit /b %BUILD_RESULT%
