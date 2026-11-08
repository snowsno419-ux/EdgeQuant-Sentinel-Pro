@echo off
setlocal
title Screen off after 5 minutes; keep laptop awake (plugged in)
echo ==========================================================
echo   SCREEN OFF, LAPTOP STAYS AWAKE WHILE PLUGGED IN
echo ==========================================================
echo This changes the CURRENT Windows power plan for AC power only:
echo   - display turns off after 5 minutes of inactivity
echo   - system sleep is set to Never while plugged in
echo Battery sleep, hibernation, and lid-close actions are unchanged.
echo Keep the charger connected and the laptop lid open.
echo.
choice /C YN /M "Apply these two AC power settings"
if errorlevel 2 goto cancelled

echo.
powercfg /change monitor-timeout-ac 5
if errorlevel 1 goto failed
powercfg /change standby-timeout-ac 0
if errorlevel 1 goto failed
powercfg /setactive SCHEME_CURRENT
if errorlevel 1 goto failed

echo.
echo DONE. The screen should turn off after 5 idle minutes; the laptop will not sleep while plugged in.
echo Keep the lid open for ventilation. On battery, your existing sleep setting still applies.
echo To reverse the change, open Settings - System - Power - Screen and sleep and restore your preferred plugged-in timeouts.
echo.
pause
exit /b 0

:cancelled
echo Cancelled; no settings changed.
pause
exit /b 0

:failed
echo One or more power settings could not be changed.
echo Right-click this BAT file, choose Run as administrator, and try once more.
echo No hibernation or lid-close setting was intentionally changed.
echo.
pause
exit /b 1
