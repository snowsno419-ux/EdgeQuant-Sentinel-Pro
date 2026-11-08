# EdgeQuant Sentinel Pro — UI redesign (Python Tkinter)

This build retains the original Python `edgequant_auto.py` trading engine and all existing UI handlers. It does **not** use Electron or Node.js.

## New design
- New **SENTINEL PRO** navy/cyan/violet palette and larger table rows.
- Simplified sidebar: Dashboard, Channels, Brokers/MT5, Trade Journal first, with advanced features retained below.
- New 5-card status ribbon on the Dashboard: account balance, equity, floating P&L, pending orders and MT5 connection.
- The existing daily LIMIT order report, break-even layer selector (SIGNAL/QUICK/ALL), charts, and controls are retained.
- All status ribbon values are read from current application state; offline broker values display em dashes rather than fabricated profits.

## Use
Run `EDGEQUANT-APP.bat` and select **SENTINEL PRO** in the theme selector. Existing saved theme choices are preserved; new installs default to SENTINEL PRO.

## Verification
Python syntax compilation was checked. Windows Tkinter rendering, live Telegram and MT5 order execution have **not** been verified here. Test with an MT5 demo account before live use.
