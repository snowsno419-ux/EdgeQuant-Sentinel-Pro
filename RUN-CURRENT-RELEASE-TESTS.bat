@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if errorlevel 1 (
  echo ERROR: Could not enter the extracted project directory.
  pause
  exit /b 80
)
echo EdgeQuant CURRENT RELEASE regression tests (offline; NO LIVE MT5 ORDERS)
call "%~dp0PREPARE-CLIENT-BUILD-ENV.bat"
if errorlevel 1 (
  echo FAIL: Build/test Python dependencies unavailable.
  pause
  exit /b 18
)
set "PATH=%BUILD_ENV_DIR%\Scripts;%PATH%"
python -m unittest discover -s . -p "test_*.py" -v
set "TEST_RESULT=%ERRORLEVEL%"
echo.
if "%TEST_RESULT%"=="0" (
  echo PASS: All current-release regression tests passed.
) else (
  echo FAIL: Regression tests failed; do not distribute installer.
)
echo This window stays open. Press a key to close.
pause
exit /b %TEST_RESULT%
