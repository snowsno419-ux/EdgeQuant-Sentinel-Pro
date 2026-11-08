# EdgeQuant Sentinel | Client Installer Windows XLSX File Lock Fix

Date: 2026-11-06

## Reported failure

Running the source-free Client Installer builder on Windows failed in the offline test stage with:

    PermissionError: [WinError 32] ... Temp\edgequant-provider-v510-...\provider.xlsx
    Ran 191 tests ... FAILED (errors=2)
    STOP: CURRENT RELEASE offline regression tests failed. (exit code 9)

This is NOT evidence of an MT5 broker failure. The error arose before the installer could build.

## Confirmed code defect and fix

- In `test_provider_studio_v510.py`, the test for the branded Provider Excel export used `self.addCleanup(workbook.close)` while running inside `tempfile.TemporaryDirectory()`.
- `unittest.addCleanup` executes after the test method returns, but the temporary directory is deleted when its `with` block exits. On Windows, an open openpyxl `read_only=True` workbook can hold a ZIP file lock, so deletion raises `WinError 32`.
- Changed the test to use `with contextlib.closing(load_workbook(...))` INSIDE the TemporaryDirectory block. This closes the workbook even if an assertion fails.
- Added an explicit try/finally close to the frozen-app XLSX smoke-check in `edgequant_desktop.py`.
- Added `test_windows_provider_xlsx_lock_20261106.py`. It checks that all read-only XLSX file handles have closed before temp-dir cleanup; the test fails with the previous code even on Linux, and passes with the fix.
- Existing installer pre-build tests remain enabled. Errors are not suppressed and no acceptance gate was bypassed.

## Test evidence

- Cross-platform source test suite: 198 tests passed after patch (Python runtime in this environment, not Windows).
- Regression test: FAILED before the fix (unclosed provider.xlsx), PASSED after the fix.
- Python core syntax compilation: PASS.
- Windows native installer build, Inno Setup output, MetaTrader5 import, and client clean-PC test: NOT performed here.
- The screenshot reports 2 errors. The file-lock error shown is fixed; if Windows still reports another error, share `CLIENT-INSTALLER-BUILD.log` so the remaining stack trace can be diagnosed. Do not distribute a failed build.

## How to install/build (Windows)

1. Stop the existing EdgeQuant app and save a copy of the old project. Keep your Telegram sessions, MT5 account configs, and private settings outside the build source ZIP if possible.
2. Extract this ZIP into a short writable directory such as `C:\EdgeQuantBuild` (do not run from inside the ZIP).
3. Open the extracted `EdgeQuant-Sentinel-Universal-Engine-PRIVATE-GROUP-DASHBOARD-DEV` folder.
4. Double click `RUN-CLIENT-INSTALLER-KEEP-OPEN.bat`.
5. A successful build creates `dist\EdgeQuant-Sentinel-Client-Setup.exe` after the pre-build tests, EXE build, scrub, smoke checks, and Inno Setup pass.
6. If the build stops, read `CLIENT-INSTALLER-BUILD.log` in the project folder and send the complete error text. `error code 9` means the offline regression tests failed (not necessarily the same cause as before).

Never distribute an incomplete `dist` folder or build outputs until all release gates pass and a clean Windows demo test succeeds.
