# EdgeQuant Client Installer: Windows batch label and diagnostics fix

## Confirmed from the user's diagnostic report (2026-11-06)

- Windows 11 x64 and Inno Setup 6 are present.
- The private build virtual environment uses Python 3.12 x64.
- `cryptography`, `requests`, Pillow, openpyxl and MetaTrader5 installed successfully.
- The actual blocker occurs after the MetaTrader5 native import check:
  `The system cannot find the batch label specified - build`
- `BUILD-EXE.bat` had a `goto build` and a `:build` label, but the file was LF-only (`\n`), which breaks label navigation on Windows CMD under this invocation.

## Fixes

1. Normalize ALL `.bat` files to standard CRLF Windows line endings. **Do not save them as LF-only from an editor.**
2. Repair `EDGEQUANT-INSTALLER-DIAGNOSIS.ps1` so Python probes do not embed double-quoted strings that were lost through native command line argument escaping.
3. Rewrite `RUN-CLIENT-INSTALLER-LOGGED.ps1` to write a single consistently encoded UTF-8 log (instead of appending UTF-16 from Tee-Object to a UTF-8 header).
4. Add release regression tests to catch LF-only batch files and missing `goto build`/`:build` labels in future packages.

## Installation

1. Stop EdgeQuant. Back up any local configuration, Telegram sessions, and journal data in the old directory.
2. Extract the **complete** ZIP to a fresh folder such as `C:\EQBuild\EdgeQuant`. Do not overwrite an existing extracted project with locked files.
3. Run `RUN-CLIENT-INSTALLER-KEEP-OPEN.bat` (or `BUILD-CLIENT-INSTALLER.bat`).
4. On success, the installer should be in `dist\EdgeQuant-Sentinel-Client-Setup.exe`.
5. On any further failure, run `CHECK-INSTALLER-ERROR.bat` and check `CLIENT-INSTALLER-BUILD.log` before distributing anything.

## Important scope

Batch-format and logging fixes only; no trading logic or risk limits were changed. The source ZIP contains the previous fixes from the input version. Python offline tests cannot guarantee that PyInstaller and Inno Setup finish successfully on a specific Windows PC; test the result on a clean Windows system and MT5 demo account first.
