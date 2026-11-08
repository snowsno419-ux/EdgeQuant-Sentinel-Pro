@echo off
setlocal
cd /d "%~dp0"
title EdgeQuant Sentinel Pro - Desktop
set "EQ_PY="
py -3.12 -c "import MetaTrader5" >nul 2>nul
if not errorlevel 1 set "EQ_PY=py -3.12"
if not defined EQ_PY (
  python -c "import MetaTrader5" >nul 2>nul
  if not errorlevel 1 set "EQ_PY=python"
)
if not defined EQ_PY (
  echo [EdgeQuant] MetaTrader5 connector is unavailable in the selected Python.
  echo [EdgeQuant] Install on Python 3.12: py -3.12 -m pip install MetaTrader5 telethon
  echo [EdgeQuant] The app will start for diagnostics; trading may remain unavailable.
  py -3.12 --version >nul 2>nul
  if not errorlevel 1 set "EQ_PY=py -3.12"
)
if not defined EQ_PY set "EQ_PY=python"
echo [EdgeQuant] Starting with %EQ_PY%
%EQ_PY% edgequant_desktop.py
if errorlevel 1 (
  echo.
  echo [EdgeQuant] Startup failed. Review the message above and edgequant_error.log.
  pause
)
endlocal
