@echo off
setlocal
cd /d "%~dp0"
python test_telegram_code_guard.py
if errorlevel 1 (
 echo Telegram login offline tests failed.
 exit /b 1
)
echo.
echo Telegram login offline tests passed. No real Telegram code was requested.
pause
