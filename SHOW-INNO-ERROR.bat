@echo off
setlocal
cd /d "%~dp0"
echo =============================================================
echo  EdgeQuant Inno Setup Compiler - Detailed Error Report
echo =============================================================
if not exist "INNO-COMPILER-ERROR.log" (
 echo [ERROR] No compiler log yet. Run RUN-CLIENT-INSTALLER-KEEP-OPEN.bat first.
) else (
 powershell.exe -NoProfile -Command "Get-Content -LiteralPath 'INNO-COMPILER-ERROR.log' -Tail 100"
)
echo.
echo To share this log, send INNO-COMPILER-ERROR.log (redact secrets).
echo.
pause
exit /b 0
