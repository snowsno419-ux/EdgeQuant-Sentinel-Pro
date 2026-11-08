# EdgeQuant Setup - DeleteFile failed (code 5, Access is denied)

Observed file: `%LOCALAPPDATA%\Programs\EdgeQuant Sentinel\_internal\libcrypto-3.dll`.

## Existing Setup.exe: immediate recovery

1. DO NOT select `Skip this file`. It may leave mismatched DLLs.
2. Review MT5 exposure and STOP the EdgeQuant engine safely. Stop auto-trading before exiting.
3. Close EdgeQuant completely, including tray windows / any extra EdgeQuantSentinel.exe.
4. Return to installer and select `Try again`. If it fails, cancel setup, reboot, and rerun setup **before launching EdgeQuant**.
5. If it still fails after reboot, inspect `resmon.exe > CPU > Associated Handles`, search `libcrypto-3.dll`; investigate locked process or incorrect folder ACLs. Do not blindly delete `_internal` or `.session` data.

Optional `EDGEQUANT-STOP-FOR-UPDATE.bat` lists EdgeQuant process IDs; it will not terminate them unless user enters `CLOSE`. Never force-close an actively trading bot without reviewing open positions.

## New builds: preventative change

- Explicit Inno Setup `CloseApplicationsFilter` includes DLL/PYD files.
- `AppMutex` detects instances of updated EdgeQuant client still running.
- Matching named Windows mutex created by actual GUI `edgequant_desktop.py` process.
- No automated taskkill or permission modifications during install.
- Older installations do not create the new mutex, so on the *first* upgrade, manual close/reboot may still be needed.

## Verification

- Static checks: .iss guard and Python mutex name match; Python compiles.
- This environment cannot run the Windows Inno compiler or validate a live client install. Validate on an actual Windows demo installation before release.
