EDGEQUANT SENTINEL v1.9.12 — UNIVERSAL BROKER SYMBOL CHOOSER
Source update pack, 2026-10-22

WHAT CHANGED
- Removed the desktop account-add/remove form. Existing saved account settings are preserved; if an app-saved broker exists and no static account is configured, the saved account list becomes the default without adding a phantom MAIN target.
- In the desktop BROKERS tab, set an exact gold symbol for each saved MT5 account: AUTO, XAUUSD, XAUUSDm, XAUUSDc, or another exact Market Watch name.
- The choice is stored locally in edgequant_broker_symbols.json and applies to every signal group routed to that account. XAUUSDc is an available choice, not a hardcoded default.
- An explicit symbol choice is exact. If that name is missing from the selected MT5 account, that account is skipped; the engine does not silently guess another suffix.
- Any placed signal missing either SL or TP is sent to manual review for every user-added source, except when the message explicitly says MARKET, NOW, or INSTANT and the existing automatic-protection path applies.
- Different Telegram posts are independent signals, even if the text/prices match. Only exact replay of the same Telegram chat ID + message ID is blocked. Posts are not concatenated and old messages are not replayed.

PRESERVE YOUR EXISTING DATA
This source-only ZIP intentionally excludes config.json, edgequant_desktop.json, edgequant_state.json, edgequant_brokers.json, Telegram session/credential files, trade history, and logs. Do not replace, delete, or upload those files. Keep your existing channels, broker routes, API credentials, and other account settings.

This is not a ready-built Windows EXE and is not a one-click installer. Back up your current application folder first. If your local Python files contain manual changes, merge carefully rather than overwriting them wholesale. After updating the source, run the offline checks and rebuild the EXE on the Windows machine using BUILD-EXE.bat. The current Windows runtime/EXE has not been updated or verified by this sandbox.

VALIDATION (offline only)
- edgequant_auto.py --selftest: 538 passed, 0 failed
- edgequant_desktop.py --selfcheck: 300 passed, 0 failed
- test_parser.py: 41/41 passed
- Python compilation and edgequant_check.py: passed
- Per-account resolution used fake MT5 APIs only. No live MT5 order or Telegram send was attempted.

NO SECRETS OR LIVE ACTIONS
No client credentials, session files, broker passwords, active channel data, account state, or real trade history are included. Do not put credentials into this archive. Selecting or saving a symbol does not connect to MT5 or send an order.
