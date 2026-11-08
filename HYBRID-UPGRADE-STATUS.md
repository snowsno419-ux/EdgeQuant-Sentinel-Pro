# EdgeQuant Sentinel — Hybrid Upgrade Work Log

Date: 2026-11-01
Package: source development build

## Source inspection

- Uploaded archive passed `ZipFile.testzip()` with no corrupt entries.
- 82 archive entries were present at intake.
- Actual project root: `EdgeQuant-Sentinel-Universal-Engine-PRIVATE-GROUP-DASHBOARD-DEV`.
- Desktop is a large Tkinter application (`edgequant_desktop.py`); no Electron, React, TypeScript, Vite, or package.json scaffold exists in this upload.
- Python execution engine is `edgequant_auto.py`; parser is `signal_parser.py`.
- MT5 and Telegram integration code is present.
- Existing dashboard already reads live MT5 quotes and calculates M5/M15/H1/H4 EMA-based trend snapshots.
- Existing spread guard, review handling, voice features, Telegram Studio, and installer scripts are present.
- Existing installer recipe: `EdgeQuantSentinel-Client.iss`, plus `BUILD-CLIENT-INSTALLER.bat` and `BUILD-EXE.bat`.

## Implemented in this update

1. Pending-order planning no longer automatically converts a requested XAUUSD BUY LIMIT / SELL LIMIT into STOP.
2. A LIMIT whose exact entry is invalid against the current quote or broker stop distance is retained at the original price/type and routed to Manual Review for both layers.
3. A fixed Gold LIMIT whose adjusted entry crosses the original signal SL is routed to Manual Review for both layers.
4. Immediately before submission, the engine rechecks the exact requested pending type against fresh Bid/Ask and broker stop/freeze distance. If no longer valid, the order is put into Manual Review; no type conversion or repricing occurs.
5. The dashboard now displays full trend names: BULLISH, BEARISH, SIDEWAYS, UNAVAILABLE. Bullish is green, bearish red, and sideways/unavailable grey.
6. Updated the related pytest expectations and engine self-test assertions to match the confirmed owner rules.
7. Timestamped pre-edit backups are in `BACKUP_BEFORE_HYBRID_UPGRADE/`.

## Validation actually run

- `python -m pytest -q --disable-warnings`: 61 passed, 11 subtests passed.
- `python edgequant_auto.py --selftest`: 555 passed, 0 failed.
- `python edgequant_desktop.py --selfcheck`: 324 passed, 0 failed.
- `python edgequant_desktop.py --xlsx-selfcheck`: passed.
- ZIP integrity: passed on the source archive and updated package.
- Python syntax compilation: run on changed Python files.

## Environment limitations / remaining work

- `MetaTrader5` and `telethon` Python packages are not installed in this environment. Live MT5 and Telegram integration were not exercised.
- No Windows environment is available here; EXE and Inno Setup installer were not built or smoke-tested.
- The source checker reports those missing optional/runtime dependencies and emits an old-package warning about `EDGEQUANT-VERSION.bat`, which is not present in the uploaded archive. The checker output is not evidence of a live broker test.
- Electron + React + TypeScript migration has NOT been implemented in this phase. The uploaded project has no Electron scaffold. A secure bridge must be designed against the actual engine/UI lifecycle before wiring a renderer; a mock dashboard or disconnected Electron shell would violate the handover requirements.
- No live-money execution was used.

## Safety note

This package is a source development update, not a production-certified release. Before live use, verify on a Windows machine with the user's MT5 demo account, Telegram login, broker symbol specifications, and a clean Windows installation.
