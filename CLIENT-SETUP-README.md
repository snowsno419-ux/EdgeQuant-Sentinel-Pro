# EdgeQuant Sentinel client installer — build instructions

## Current status

This is a Windows **build kit**, not a finished Setup.exe. It has not been compiled or run on Windows in this Linux workspace. A Sinhala step-by-step guide is included as `CLIENT-BUILD-GUIDE-SI.txt`. Do not distribute a client installer until the build passes on a Windows 10/11 x64 PC and has been installed/tested on a clean Windows PC without Python.

## Intended client install

- Per-user installation under `%LOCALAPPDATA%\Programs\EdgeQuant Sentinel`; no administrator prompt is intended.
- The PyInstaller onedir package bundles Python and the application dependencies. Client PCs do not need system Python or pip, and the installer does not download Python/libraries at install time.
- Each client enters their own Telegram/MT5 details. Do not package anyone's credentials, Telegram session, account config, settings, journals, logs, or Provider data.
- The MT5 desktop terminal is separate software and must be installed/logged in by the client if they use MT5 features.
- The optional offline female Sinhala VITS worker/model installer is excluded from this first source-free client build; standard built-in voice clips/SAPI functions remain.
- All `.py` and `.pyw` files are removed from the temporary `dist` payload, and the Inno Setup file excludes `.py`/`.pyw` as an additional safeguard. A compiled Python app is not impossible to reverse engineer; do not treat PyInstaller as cryptographic protection for trade logic or secrets.
- No license/activation step is added, per the owner's choice.
- Telegram auto-reconnect is mandatory: transient network loss retries automatically with a capped delay, including startup connection failures when an existing session is present. Reconnect history is rechecked through normal message-ID/freshness and trading safety gates. A revoked/expired login or missing first-time login still needs the client to complete LOGIN; reconnect cannot bypass Telegram authorization.

## Build steps (owner/developer Windows PC only)

1. Use a Windows 10/11 x64 PC with internet access. Install 64-bit Python with Tcl/Tk and install Inno Setup 6. These are build tools only; clients do not need them.
2. Extract the complete owner source/build kit to a writable local folder (not `Program Files`, OneDrive, or a network share). Keep the existing personal credentials/settings/session files out of the source kit.
3. Double-click `BUILD-CLIENT-INSTALLER.bat` and follow its prompts. The client wrapper runs the offline tests, builds the frozen app without launching a developer UI, scrubs the temporary payload, performs packaged smoke checks, and compiles the installer.
4. The wrapper scrubs project `.py` source files, local settings, account/session data and logs **from `dist` only**, then reruns the MT5 `_core` import-only check and Provider/Plan Excel logo check. No terminal initialize, account login, Telegram send, or MT5 order is part of those two checks.
5. If all checks pass and Inno Setup is installed, the wrapper creates `dist\EdgeQuant-Sentinel-Client-Setup.exe`. Give clients only that Setup.exe—not the source kit and not the `dist` folder.
6. Before distribution, test the Setup.exe on a clean Windows 10/11 x64 PC with no system Python. Confirm install/uninstall, first-run setup, settings save/reload, Telegram login, and MT5 demo/TEST behavior. Do not place a live order during testing.

## Important limitation

The Windows build and installer have **not** been validated here. If any stage fails, stop and retain the full error text; do not distribute the partial `dist` folder. The user's existing `BUILD-EXE.bat` remains a source/developer build and should not be sent to clients.
