# EdgeQuant brand icon and automatic desktop shortcut (7 November 2026)

## Changes
- Uses the **existing official EdgeQuant EQ** `edgequant-icon.ico` asset already bundled with the source. No invented/replacement logo.
- `BUILD-EXE.bat` now passes `--icon "edgequant-icon.ico"` to PyInstaller so the frozen `EdgeQuantSentinel.exe` embeds the EQ icon.
- `EdgeQuantSentinel-Client.iss` now sets explicit `IconFilename: "{app}\edgequant-icon.ico"` for both Desktop and Start Menu shortcuts.
- The desktop shortcut is **always created** during installation/upgrade (no unchecked optional desktop-icon task).
- The EXE build validates the icon file exists in the `dist\EdgeQuantSentinel` app payload. The prior `--add-data` and copy steps keep this asset installed.
- Setup already has `SetupIconFile=edgequant-icon.ico` and `UninstallDisplayIcon={app}\EdgeQuantSentinel.exe`.

## Build and verify on Windows
1. Extract the **entire** ZIP to a new short directory, e.g. `C:\EQBrandBuild`, and open its `EdgeQuant` folder. Avoid merging into an old extracted source directory.
2. Stop the installed EdgeQuant before updating, and back up client settings/session first.
3. Run `RUN-CLIENT-INSTALLER-KEEP-OPEN.bat` on the build PC, and verify the full build succeeds.
4. Install the newly built `dist\EdgeQuant-Sentinel-Client-Setup.exe`, then check the Desktop, Start Menu, and executable icon.
5. If Windows Explorer still displays the old cached shortcut icon, refresh the Desktop or sign out and back in; verify the shortcut's `Properties > Shortcut > Change Icon` points to the installed `edgequant-icon.ico`.

This ZIP is source only. The Windows PyInstaller/Inno Setup build and installed-shell icon display cannot be run inside this Linux environment. The actual installer and client environment must be smoke-tested on Windows. All trading and Telegram behavior was left unchanged by this change.
