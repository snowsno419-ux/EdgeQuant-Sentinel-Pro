@echo off
title EdgeQuant Sentinel - build source-free client installer
cd /d "%~dp0"
echo.
echo   EDGEQUANT SENTINEL - CLIENT INSTALLER BUILDER
echo   ------------------------------------------------
echo   Developer/build PC only. Clients receive only the generated Setup.exe.
echo   The client installer bundles the Python runtime and app libraries.
echo   A client PC does not need system Python.
echo   Build PC: Windows 10/11 x64, Python 64-bit + Tcl/Tk, internet, Inno Setup 6.
echo.
echo   NOTE: the existing build will briefly create a local dist folder that contains
echo   source-mode files. The script scrubs those files and local settings/sessions
echo   from dist before the installer is compiled. Do not distribute dist before it
echo   reports SCRUB + INSTALLER BUILD PASSED.
echo.
echo   [PRECHECK] Looking for Inno Setup 6 before spending time on the build...
set "ISCC="
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not defined ISCC if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not defined ISCC for /f "delims=" %%I in ('where ISCC.exe 2^>nul') do if not defined ISCC set "ISCC=%%I"
if not defined ISCC goto no_inno
rem Ensure all dependencies, including Ed25519 cryptography, are ready BEFORE test discovery.
rem A private venv also avoids accidental use of incompatible Python 3.15.
call "%~dp0PREPARE-CLIENT-BUILD-ENV.bat"
if errorlevel 1 goto build_dependencies_fail
set "PATH=%BUILD_ENV_DIR%\Scripts;%PATH%"
python -c "import struct, tkinter, _tkinter; assert struct.calcsize('P') == 8; print('64-bit Python and Tcl/Tk OK')"
if errorlevel 1 goto build_prereq_fail

echo.
echo   [0/5] Running CURRENT RELEASE offline regression suite (all test_*.py)...
echo   This suite includes Telegram reconnect, exact LIMIT prices, broker order mocks,
echo   multilingual edits, AI Agent removal, trading caps and the updated signal-SL rule.
python -m unittest discover -s . -p "test_*.py" -v
if errorlevel 1 goto release_tests_fail
python -m py_compile edgequant_auto.py edgequant_duplicate_guard.py edgequant_desktop.py edgequant_vip_format.py edgequant_vip_signal_edits.py
if errorlevel 1 goto release_tests_fail
echo.
echo   PASS: current-release regression suite + core Python syntax checks.
echo   NOTE: the older edgequant_auto.py --selftest contains pre-change LIMIT
echo   assumptions and is NOT the current-release installer acceptance gate.


echo.
echo   [1/5] Building and smoke-testing the frozen app...
set "EDGEQUANT_CLIENT_BUILD=1"
call "%~dp0BUILD-EXE.bat"
set "EDGEQUANT_CLIENT_BUILD="
if errorlevel 1 goto fail_build
if not exist "%~dp0dist\EdgeQuantSentinel\EdgeQuantSentinel.exe" goto missing_exe

echo.
echo   [2/5] Removing project source files and local user data from dist only...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0SCRUB-CLIENT-DIST.ps1"
if errorlevel 1 goto scrub_fail

echo.
echo   [3/5] Re-testing the source-scrubbed app (MT5 import-only; Excel export only)...
"%~dp0dist\EdgeQuantSentinel\EdgeQuantSentinel.exe" --mt5-import-selfcheck
if errorlevel 1 goto mt5_fail
if not exist "%~dp0dist\EdgeQuantSentinel\mt5-import-selfcheck.log" goto mt5_fail
findstr /B /C:"PASS | MetaTrader5 _core import succeeded" "%~dp0dist\EdgeQuantSentinel\mt5-import-selfcheck.log" >nul
if errorlevel 1 goto mt5_fail
"%~dp0dist\EdgeQuantSentinel\EdgeQuantSentinel.exe" --xlsx-selfcheck
if errorlevel 1 goto xlsx_fail
if not exist "%~dp0dist\EdgeQuantSentinel\xlsx-selfcheck.log" goto xlsx_fail
findstr /B /C:"PASS | provider and plan Excel exports opened successfully with logos" "%~dp0dist\EdgeQuantSentinel\xlsx-selfcheck.log" >nul
if errorlevel 1 goto xlsx_fail

del /q "%~dp0dist\EdgeQuantSentinel\mt5-import-selfcheck.log" >nul 2>nul
del /q "%~dp0dist\EdgeQuantSentinel\xlsx-selfcheck.log" >nul 2>nul
del /q "%~dp0dist\EdgeQuantSentinel\edgequant_startup.log" >nul 2>nul

echo.
echo   [4/5] Compiling source-scrubbed Windows Setup.exe with Inno Setup...
echo   This step will print ALL compiler errors and write INNO-COMPILER-ERROR.log.
set "INNO_DIAG_LOG=%~dp0INNO-COMPILER-ERROR.log"
if exist "%INNO_DIAG_LOG%" del /q "%INNO_DIAG_LOG%" >nul 2>nul
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0COMPILE-INNO-DIAGNOSTICS.ps1" -CompilerPath "%ISCC%" -ScriptPath "%~dp0EdgeQuantSentinel-Client.iss" -LogPath "%INNO_DIAG_LOG%"
if errorlevel 1 goto inno_fail
if not exist "%~dp0dist\EdgeQuant-Sentinel-Client-Setup.exe" goto inno_fail

echo.
echo   ================================================================
echo    CLIENT SETUP READY:
echo    %~dp0dist\EdgeQuant-Sentinel-Client-Setup.exe
echo   ================================================================
echo   Give clients ONLY the Setup.exe. Do not send the source ZIP or dist folder.
echo   Install/test on a clean Windows 10/11 x64 PC without Python before distribution.
echo   MT5 desktop terminal and the client's own Telegram/MT5 accounts are separate.
echo   Optional offline female VITS Sinhala worker is not in this client build.
echo.
rem Outer installer launcher keeps the window open.
exit /b 0

:build_prereq_fail
echo.
echo   STOP: install 64-bit Windows Python with Tcl/Tk before building.
echo   The client PC still does NOT need Python.
echo.
rem Outer installer launcher keeps the window open.
exit /b 17

:no_inno
echo.
echo   STOP: Inno Setup 6 (ISCC.exe) was not found on this build PC.
echo   Install Inno Setup 6, then run this builder again. Client PCs do NOT need Inno Setup.
echo.
rem Outer installer launcher keeps the window open.
exit /b 10
:missing_exe
echo.
echo   STOP: the frozen application was not created. Review BUILD-EXE.bat output.
echo.
rem Outer installer launcher keeps the window open.
exit /b 11
:scrub_fail
echo.
echo   STOP: source/runtime scrub failed. Do NOT distribute any dist files.
echo.
rem Outer installer launcher keeps the window open.
exit /b 12
:mt5_fail
echo.
echo   STOP: the source-scrubbed frozen MetaTrader5 import-only check failed.
echo   No account login, MT5 initialize or order was requested by this client-builder step.
echo.
rem Outer installer launcher keeps the window open.
exit /b 13
:xlsx_fail
echo.
echo   STOP: the source-scrubbed Provider/Plan Excel logo check failed.
echo.
rem Outer installer launcher keeps the window open.
exit /b 14
:inno_fail
echo.
echo   STOP: Inno Setup could not compile the client installer.
echo   INNO COMPILER ERROR: read "%~dp0INNO-COMPILER-ERROR.log".
echo   The log includes the exact compiler error, code and source line.
echo   Do NOT distribute the dist folder.
echo.
rem Outer installer launcher keeps the window open.
exit /b 15

:build_dependencies_fail
echo.
echo   STOP: The private Python build environment is not ready.
echo   See PREPARE error above; do NOT build or distribute.
echo.
exit /b 18

:release_tests_fail
echo.
echo   STOP: CURRENT RELEASE offline regression tests failed. Do NOT build or distribute.
echo.
rem Outer installer launcher keeps the window open.
exit /b 9
:fail_build
echo.
echo   STOP: BUILD-EXE.bat failed or was cancelled. Do NOT distribute any dist files.
echo.
rem Outer installer launcher keeps the window open.
exit /b 1

:strategy_tests_fail
echo.
echo   STOP: offline engine strategy tests failed. Do NOT build or distribute.
echo.
rem Outer installer launcher keeps the window open.
exit /b 16
