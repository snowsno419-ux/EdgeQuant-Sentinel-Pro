@echo off
rem Prepare a private Windows build venv. Called from BUILD-CLIENT-INSTALLER-CORE.bat.
rem It must be called, so BUILD_ENV_DIR is kept in the caller's environment.
set "BUILD_ENV_DIR=%~dp0.edgequant-build-venv"
set "BUILD_ENV_PY=%BUILD_ENV_DIR%\Scripts\python.exe"
echo.
echo   [PREPARE] Isolated build Python (no global pip changes)...
if exist "%BUILD_ENV_PY%" goto check_existing

set "EQ_PY_LAUNCH="
where py >nul 2>nul
if errorlevel 1 goto try_plain_python
py -3.11 -c "import struct; assert struct.calcsize('P') == 8" >nul 2>nul
if not errorlevel 1 set "EQ_PY_LAUNCH=py -3.11"
if defined EQ_PY_LAUNCH goto create_venv
py -3.12 -c "import struct; assert struct.calcsize('P') == 8" >nul 2>nul
if not errorlevel 1 set "EQ_PY_LAUNCH=py -3.12"
if defined EQ_PY_LAUNCH goto create_venv
py -3.13 -c "import struct; assert struct.calcsize('P') == 8" >nul 2>nul
if not errorlevel 1 set "EQ_PY_LAUNCH=py -3.13"
if defined EQ_PY_LAUNCH goto create_venv
py -3.14 -c "import struct; assert struct.calcsize('P') == 8" >nul 2>nul
if not errorlevel 1 set "EQ_PY_LAUNCH=py -3.14"
if defined EQ_PY_LAUNCH goto create_venv

:try_plain_python
where python >nul 2>nul
if errorlevel 1 goto python_missing
python -c "import sys,struct; assert (3,11)<=sys.version_info[:2]<=(3,14) and struct.calcsize('P')==8" >nul 2>nul
if errorlevel 1 goto python_missing
set "EQ_PY_LAUNCH=python"

:create_venv
echo   Using %EQ_PY_LAUNCH% to create %BUILD_ENV_DIR%
%EQ_PY_LAUNCH% -m venv "%BUILD_ENV_DIR%"
if errorlevel 1 goto venv_failed
if not exist "%BUILD_ENV_PY%" goto venv_failed

:check_existing
"%BUILD_ENV_PY%" -c "import sys,struct; assert (3,11)<=sys.version_info[:2]<=(3,14) and struct.calcsize('P')==8; print('Build Python:',sys.version.split()[0],sys.executable)"
if errorlevel 1 goto bad_venv
"%BUILD_ENV_PY%" -m pip --version
if errorlevel 1 goto pip_failed
echo   [PREPARE] Installing / verifying all runtime and test dependencies...
"%BUILD_ENV_PY%" -m pip install --disable-pip-version-check --no-input -r "%~dp0requirements-build.txt"
if errorlevel 1 goto pip_failed
"%BUILD_ENV_PY%" -c "import cryptography, requests, telethon, openpyxl, et_xmlfile, PIL, PyInstaller; from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey; print('PASS: cryptography / requests / Telethon / Excel / PyInstaller imports')"
if errorlevel 1 goto pip_failed
echo   [PREPARE] Build environment ready. Tests will now run.
exit /b 0

:python_missing
echo.
echo   STOP: Python 3.11, 3.12, 3.13, or 3.14 x64 was not found.
echo   Python 3.15 cannot build this MT5 client (no cp315 Windows wheel).
echo   Install Python 3.11 x64 with Tcl/Tk and pip, then re-run.
exit /b 21
:venv_failed
echo.
echo   STOP: Could not create private build environment.
echo   Check folder permissions, Python installation and available disk space.
exit /b 22
:bad_venv
echo.
echo   STOP: An existing .edgequant-build-venv has an unsupported/broken Python.
echo   Rename this build-only folder and re-run with Python 3.11 x64 installed.
exit /b 23
:pip_failed
echo.
echo   STOP: Required build dependencies could not be installed/loaded.
echo   Check pip's error above and internet access; do not distribute a partial build.
exit /b 24
