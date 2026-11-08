@echo off
title EdgeQuant - build EdgeQuantSentinel.exe
cd /d "%~dp0"
echo.
echo   EdgeQuant Desktop  -^>  .exe        (v1.9.12 UI V5.1.13)
echo   --------------------------------------------------
echo   IMPORTANT: the old v1.6.4 EXE can fail with "lost sys.stdin".
echo   This V5.1.13 build includes reverse offsets, no price-run skip, and explicit basic-group
echo   account sending; channel/supergroup Send As remains permission-checked and fail-closed.
echo   This needs internet (it downloads PyInstaller).
echo   It takes 1-3 minutes.  Keep this window open.
echo.
python -c "from pathlib import Path; a=Path('edgequant_auto.py').read_text(encoding='utf-8'); d=Path('edgequant_desktop.py').read_text(encoding='utf-8'); assert 'VERSION = ' + chr(34) + '1.9.12' + chr(34) in a; assert 'APP_BUILD = ' + chr(34) + 'desktop 1.9.12 UI-V5.1.13' in d"
if errorlevel 1 goto wrongsource
python -c "import struct; assert struct.calcsize('P') == 8, 'Use 64-bit Python for MetaTrader5'; print('Python architecture: 64-bit')"
if errorlevel 1 goto not64
python -c "import tkinter, _tkinter; print('Tcl/Tk OK', _tkinter.TCL_VERSION, _tkinter.TK_VERSION)"
if errorlevel 1 goto notk
if not defined EDGEQUANT_CLIENT_BUILD pause
echo.
echo   [1/3] installing what the exe needs ...
rem Keep the same dependency manifest used by pre-build regression tests.
rem This also fixes missing cryptography/requests for standalone BUILD-EXE runs.
python -m pip install --disable-pip-version-check --no-input -r "requirements-build.txt"
if errorlevel 1 goto depsfail
python -c "import cryptography, requests; from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey; print('Remote envelope crypto + HTTP dependencies OK')"
if errorlevel 1 goto depsfail
python -c "import openpyxl, et_xmlfile; from openpyxl import Workbook; from io import BytesIO; b=Workbook(); s=BytesIO(); b.save(s); s.seek(0); openpyxl.load_workbook(s, read_only=True); print('Excel dependencies OK:', openpyxl.__version__)"
if errorlevel 1 goto depsfail
python -c "from PIL import Image; [Image.open(f).verify() for f in ('edgequant-logo-small.png','edgequant-logo.png')]; print('Pillow bundled brand-logo checks OK:', Image.__file__)"
if errorlevel 1 goto depsfail
python -m pip install --upgrade MetaTrader5
if errorlevel 1 goto nomt5
python -c "import MetaTrader5 as mt5; import MetaTrader5._core as core; print('MetaTrader5 native import OK:', mt5.__file__, core.__file__)"
if errorlevel 1 goto mt5importfail
goto build
:nomt5
echo.
echo   STOP: MetaTrader5 could not be installed for this Python version.
echo   Install a supported 64-bit Windows Python + MT5 package, then rerun.
echo   This build will not claim to be LIVE-ready without the MT5 module.
echo.
if not defined EDGEQUANT_CLIENT_BUILD pause
exit /b 5
:depsfail
echo.
echo   STOP: Telegram/build dependencies did not install successfully.
echo   Fix the Python/pip error above, then rerun BUILD-EXE.bat.
echo.
if not defined EDGEQUANT_CLIENT_BUILD pause
exit /b 5
:build
echo.
echo   [2/3] building (a FOLDER build: starts fast, nothing is ever missing) ...
echo.
python -m PyInstaller --noconfirm --clean --onedir --windowed --name EdgeQuantSentinel ^
 --icon "edgequant-icon.ico" ^
 --add-data "edgequant_auto.py;." ^
 --add-data "provider_studio.py;." ^
 --add-data "edgequant-logo-small.png;." ^
 --add-data "edgequant-logo.png;." ^
 --add-data "edgequant-logo-mark.png;." ^
 --add-data "edgequant-watermark.png;." ^
 --add-data "edgequant-icon.ico;." ^
 --add-data "README.md;." ^
 --add-data "SETUP.md;." ^
 --add-data "RELEASE-NOTES-1.9.12.txt;." ^
 --add-data "RELEASE-NOTES-1.9.12-V5.1.13-TELEGRAM-BASIC-GROUP-SEND.txt;." ^
 --add-data "SINHALA-OFFLINE-VOICE.md;." ^
 --add-data "INSTALL-SINHALA-FEMALE-VOICE.bat;." ^
 --add-data "edgequant_sinhala_voice_worker.py;." ^
 --add-data "supabase/schema.sql;supabase" ^
 --hidden-import tkinter --hidden-import _tkinter ^
 --hidden-import telethon --hidden-import telethon.sync ^
 --hidden-import edgequant_cloud ^
 --hidden-import edgequant_duplicate_guard ^
 --hidden-import provider_studio ^
 --hidden-import openpyxl --hidden-import et_xmlfile --hidden-import PIL --hidden-import PIL.Image ^
 --hidden-import MetaTrader5 --hidden-import MetaTrader5._core ^
 --hidden-import PIL.ImageFile --hidden-import PIL.PngImagePlugin --hidden-import PIL.JpegImagePlugin ^
 --hidden-import pyaes --hidden-import rsa ^
 --collect-all telethon --collect-all MetaTrader5 --collect-binaries MetaTrader5 --collect-all openpyxl --collect-all et_xmlfile ^
 --collect-submodules PIL --collect-all PIL ^
 edgequant_desktop.py
if errorlevel 1 goto fail
echo.
echo   [3/3] copying the files the app reads into the same folder ...
copy /y "edgequant_auto.py"       "dist\EdgeQuantSentinel" >nul
copy /y "provider_studio.py"      "dist\EdgeQuantSentinel" >nul
copy /y "edgequant-logo-small.png" "dist\EdgeQuantSentinel" >nul
copy /y "edgequant-logo.png"      "dist\EdgeQuantSentinel" >nul
copy /y "edgequant-logo-mark.png" "dist\EdgeQuantSentinel" >nul
copy /y "edgequant-watermark.png" "dist\EdgeQuantSentinel" >nul
copy /y "edgequant-icon.ico"      "dist\EdgeQuantSentinel" >nul
copy /y "README.md"              "dist\EdgeQuantSentinel" >nul
copy /y "SETUP.md"               "dist\EdgeQuantSentinel" >nul
copy /y "RELEASE-NOTES-1.9.12.txt" "dist\EdgeQuantSentinel" >nul
copy /y "RELEASE-NOTES-1.9.12-V5.1.13-TELEGRAM-BASIC-GROUP-SEND.txt" "dist\EdgeQuantSentinel" >nul
copy /y "SINHALA-OFFLINE-VOICE.md" "dist\EdgeQuantSentinel" >nul
copy /y "INSTALL-SINHALA-FEMALE-VOICE.bat" "dist\EdgeQuantSentinel" >nul
copy /y "SCREEN-OFF-KEEP-LAPTOP-ON.bat" "dist\EdgeQuantSentinel" >nul
copy /y "edgequant_sinhala_voice_worker.py" "dist\EdgeQuantSentinel" >nul
copy /y "edgequant_cloud.py"      "dist\EdgeQuantSentinel" >nul
if not exist "dist\EdgeQuantSentinel\supabase" mkdir "dist\EdgeQuantSentinel\supabase"
copy /y "supabase\schema.sql" "dist\EdgeQuantSentinel\supabase" >nul
if not exist "voice\si\update.wav" goto novvoice
xcopy /E /I /Y "voice" "dist\EdgeQuantSentinel\voice" >nul
if errorlevel 1 goto fail
if not exist "dist\EdgeQuantSentinel\voice\si\update.wav" goto fail
if not exist "dist\EdgeQuantSentinel\SCREEN-OFF-KEEP-LAPTOP-ON.bat" goto fail
if not exist "dist\EdgeQuantSentinel\edgequant-icon.ico" goto fail
if not exist "dist\EdgeQuantSentinel\EdgeQuantSentinel.exe" goto fail
echo.
echo   Checking the packaged MetaTrader5 native module (import only; no terminal connection/orders) ...
"dist\EdgeQuantSentinel\EdgeQuantSentinel.exe" --mt5-import-selfcheck
if errorlevel 1 goto mt5packfail
if not exist "dist\EdgeQuantSentinel\mt5-import-selfcheck.log" goto mt5packfail
findstr /B /C:"PASS | MetaTrader5 _core import succeeded" "dist\EdgeQuantSentinel\mt5-import-selfcheck.log" >nul
if errorlevel 1 goto mt5packfail
del /q "dist\EdgeQuantSentinel\mt5-import-selfcheck.log" >nul 2>nul
echo   Packaged MetaTrader5 _core import succeeded (no MT5 initialize or order attempted).
echo.
echo   Checking packaged Provider, daily EOD, and Plan Excel exports with embedded logos ...
del /q "dist\EdgeQuantSentinel\xlsx-selfcheck.log" >nul 2>nul
"dist\EdgeQuantSentinel\EdgeQuantSentinel.exe" --xlsx-selfcheck
if errorlevel 1 goto xlsxpackfail
if not exist "dist\EdgeQuantSentinel\xlsx-selfcheck.log" goto xlsxpackfail
findstr /B /C:"PASS | provider and plan Excel exports opened successfully with logos" "dist\EdgeQuantSentinel\xlsx-selfcheck.log" >nul
if errorlevel 1 goto xlsxpackfail
del /q "dist\EdgeQuantSentinel\xlsx-selfcheck.log" >nul 2>nul
echo   Packaged Provider + daily EOD + Plan workbooks opened successfully.
echo.
echo   ================================================================
echo    DONE.   NEW app:   dist\EdgeQuantSentinel\EdgeQuantSentinel.exe
echo    It must show:     engine v1.9.12 (desktop 1.9.12 UI-V5.1.13)
echo   ================================================================
echo.
echo   * Keep the WHOLE dist\EdgeQuantSentinel folder together.
echo   * Do NOT open the old v1.6.4 shortcut again.
echo   * Windows may warn about an unknown app -^> More info -^> Run anyway
echo   * First Telegram setup: LOGIN -^> API SETUP (your own API ID/hash) -^> SEND CODE.
echo   * If it stops: review edgequant_startup.log locally; do not share credentials or session files.
echo.
if not defined EDGEQUANT_CLIENT_BUILD (
  start "" "%~dp0dist\EdgeQuantSentinel\EdgeQuantSentinel.exe"
  pause
)
exit /b 0


:mt5packfail
echo.
echo   STOP: packaged MetaTrader5 _core failed its import-only check.
echo   Review dist\EdgeQuantSentinel\mt5-import-selfcheck.log; no terminal was initialized.
echo   Install/repair Microsoft Visual C++ x64 runtime and rebuild; do not distribute this EXE.
echo.
if not defined EDGEQUANT_CLIENT_BUILD pause
exit /b 7
:mt5importfail
echo.
echo   STOP: MetaTrader5._core failed to import in this exact 64-bit build Python.
echo   Install/repair Microsoft Visual C++ x64 runtime, then test:
echo   python -c "import MetaTrader5; import MetaTrader5._core"
echo   Microsoft runtime: https://aka.ms/vc14/vc_redist.x64.exe
echo   Do not build or distribute until the import succeeds.
echo.
if not defined EDGEQUANT_CLIENT_BUILD pause
exit /b 6
:not64
echo.
echo   STOP: MetaTrader5 needs the 64-bit Python build used here.
echo   Install 64-bit Windows Python and rerun BUILD-EXE.bat.
echo.
if not defined EDGEQUANT_CLIENT_BUILD pause
exit /b 8

:novvoice
echo.
echo   STOP: the Sinhala voice folder is missing (voice\si\update.wav).
echo   Extract the complete v1.9.12 ZIP and rerun BUILD-EXE.bat.
echo.
if not defined EDGEQUANT_CLIENT_BUILD pause
exit /b 4

:notk
echo.
echo   STOP: this Python installation cannot load Tcl/Tk (_tkinter).
echo   Repair Python -> Modify -> enable "Tcl/Tk and IDLE".
echo   Then rerun BUILD-EXE.bat. Do not ship a build that failed this check.
echo.
if not defined EDGEQUANT_CLIENT_BUILD pause
exit /b 3
:wrongsource
echo.
echo   STOP: these source files are NOT the complete v1.9.12 V5.1.13 source.
echo   Do not build an EXE from the old v1.6.4 folder.
echo   Use the complete V5.1.13 source tree before running this file.
echo.
if not defined EDGEQUANT_CLIENT_BUILD pause
exit /b 2
:xlsxpackfail
echo.
echo   STOP: the frozen EXE could not embed the bundled logo and reopen Provider/daily/Plan Excel reports.
echo   Review dist\EdgeQuantSentinel\xlsx-selfcheck.log for the Pillow/import diagnostic; do not distribute this EXE.
echo.
if not defined EDGEQUANT_CLIENT_BUILD pause
exit /b 6
:fail
echo.
echo   BUILD FAILED -^> read the lines above.
echo   Usually: no internet, or antivirus blocking PyInstaller.
echo   Close every EdgeQuant window and run BUILD-EXE.bat again.
echo.
if not defined EDGEQUANT_CLIENT_BUILD pause
exit /b 1
