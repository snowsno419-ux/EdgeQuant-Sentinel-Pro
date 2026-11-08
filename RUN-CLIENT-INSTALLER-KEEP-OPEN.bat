@echo off
cd /d "%~dp0"
echo [EdgeQuant] Opening a persistent Command Prompt for installer diagnostics...
start "EdgeQuant Client Installer - diagnostics" cmd.exe /D /K ""%~dp0BUILD-CLIENT-INSTALLER.bat""
exit /b 0
