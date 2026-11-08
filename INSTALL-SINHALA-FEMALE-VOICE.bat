@echo off
setlocal
cd /d "%~dp0"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
title Install EdgeQuant offline Sinhala female voice
echo =======================================================================
echo   EDGEQUANT  -  OFFLINE SINHALA FEMALE VOICE
echo =======================================================================
echo.
echo This installs a local female Sinhala neural voice for live reports.
echo The VITS checkpoint download is about 1 GB; PyTorch/TTS needs more disk.
echo CPU speed and RAM use are not measured and may vary by PC.
echo Text with P^&L, channel names, prices and order details stays on this PC.
echo The installer downloads software/model files from PyPI and Hugging Face.
echo No report text is sent to those sites.
echo.
choice /C YN /M "Continue with the large offline voice install"
if errorlevel 2 goto cancelled
where py >nul 2>nul
if errorlevel 1 goto nopy
py -3.11 --version >nul 2>nul
if errorlevel 1 goto no311
if not exist ".sinhala-voice-env\Scripts\python.exe" (
  echo.
  echo Creating an isolated Python 3.11 voice environment...
  py -3.11 -m venv ".sinhala-voice-env"
  if errorlevel 1 goto failed
)
set "VENV_PY=%~dp0.sinhala-voice-env\Scripts\python.exe"
if exist ".sinhala-voice-env\.edgequant_sinhala_voice_ready" del /q ".sinhala-voice-env\.edgequant_sinhala_voice_ready"
echo.
echo Installing CPU PyTorch and the Sinhala VITS speech runtime...
"%VENV_PY%" -m pip install --upgrade pip
if errorlevel 1 goto failed
"%VENV_PY%" -m pip install "numpy<2"
if errorlevel 1 goto failed
"%VENV_PY%" -m pip install "torch==2.2.2+cpu" "torchaudio==2.2.2+cpu" --index-url https://download.pytorch.org/whl/cpu
if errorlevel 1 goto failed
"%VENV_PY%" -m pip install "TTS==0.21.1" soundfile
if errorlevel 1 goto failed
echo.
echo Downloading the female Sinhala model (resume by running this installer again if interrupted)...
"%VENV_PY%" edgequant_sinhala_voice_worker.py --install --model-dir "voice\si\female_vits"
if errorlevel 1 goto failed
echo.
echo Running an offline voice test. You should hear the female Sinhala sample...
"%VENV_PY%" edgequant_sinhala_voice_worker.py --test --model-dir "voice\si\female_vits"
if errorlevel 1 goto failed
if defined LOCALAPPDATA if exist "%LOCALAPPDATA%\EdgeQuantSentinel\sinhala_voice_queue\status.json" del /q "%LOCALAPPDATA%\EdgeQuantSentinel\sinhala_voice_queue\status.json"
if defined LOCALAPPDATA if exist "%LOCALAPPDATA%\EdgeQuantSentinel\sinhala_voice_queue\worker.log" del /q "%LOCALAPPDATA%\EdgeQuantSentinel\sinhala_voice_queue\worker.log"
>".sinhala-voice-env\.edgequant_sinhala_voice_ready" echo verified by local install test

echo.
echo SUCCESS. Restart EdgeQuant, choose LANGUAGE SI, then press REFRESH in the VOICE panel.
echo Test the voice before using READ TODAY'S REPORT or starting a live session.
echo No speech-report text is uploaded; synthesis and playback happen locally.
echo.
pause
exit /b 0

:cancelled
echo Install cancelled. No packages or model files were changed.
pause
exit /b 0

:nopy
echo ERROR: The Windows Python launcher "py" was not found.
echo Install Python 3.11 (64-bit) and enable the Python launcher, then retry.
goto failed

:no311
echo ERROR: Python 3.11 (64-bit) is required for the pinned model runtime.
echo Install Python 3.11 alongside the existing EdgeQuant Python; do not remove it.
goto failed

:failed
echo.
echo The offline voice setup did not finish. Review the error above and rerun this file.
echo Existing EdgeQuant trading and English/SAPI settings were not modified.
echo If model download was interrupted, its .part file will resume on the next run.
echo.
pause
exit /b 1
