# EdgeQuant Sentinel — AWS Multi-MT5 Broker Dashboard

This is a **Python source project update** based on `EdgeQuant_Latest_AWS.zip`.
It preserves `edgequant_auto.py` and its GOLD LIMIT VIP execution / signal-update logic.

## New on Dashboard

For each verified MT5 terminal/account (MAIN, EXTRA, etc.) the dashboard displays a separate card with:

- **TODAY TRADING NET** — from this account's BUY/SELL deal records for today's **Windows server local calendar day**. Includes deal-level posted profit, commission, swap and fee; excludes deposits and withdrawals. Opening commissions can be included before a position is closed. Separately posted brokerage adjustments outside BUY/SELL deals may not be reflected.
- **FLOATING P&L** — from **all currently open positions** in that MT5 account, including manual / other EA positions, displayed in the MT5 account currency.
- **GOLD SPREAD** — this account's XAUUSD (or mapped suffix variant) Ask−Bid converted using the existing GOLD pip-size setting. Shows Bid, Ask, symbol and last tick time. The quote is marked STALE when outdated, rather than presented as live.
- Broker label, server/company, login identity, Balance, Equity and connection status.

The labels and amounts for one broker are not mixed with the other account. If connected accounts use different currencies, old combined Dashboard daily / floating P&L cards display **SEE BROKER CARDS** instead of an invalid summed USD number.

## Refresh

- With the **Windows source launcher** `EDGEQUANT-APP.bat`, each verified terminal can receive a **read-only quote/P&L monitor process** updating its quote/position data approximately every **2.5 seconds**. Today's deal history is checked approximately every **15 seconds**. Actual update rates depend on MT5/Windows scheduling and quote arrival.
- The existing MT5 snapshot remains a fallback (normally every ~30 seconds while the engine is running, ~12 seconds while stopped).
- In a frozen `.exe` build, the separate quote-sidecar is not launched; the existing per-account snapshot refresh supplies these broker cards. This update is **not** a new installer.
- When a terminal cannot be verified by its **exact path, login and broker server**, the sidecar refuses to display that terminal's quote as another broker. It never calls `order_send` or switches the trading engine's MT5 connection.

## Install / upgrade on AWS

1. **STOP auto trading** and close EdgeQuant Sentinel. Leave both MT5 terminals installed.
2. Back up your currently running EdgeQuant directory, including user settings, broker definitions and the DPAPI encrypted credential files. Keep the backup within the **same Windows user account**; do not copy Windows-DPAPI encrypted passwords to a different user expecting them to decrypt.
3. Extract the ZIP. Copy the **complete extracted Python project** over the current application source folder (or use a fresh folder and reconfigure accounts). Do **not** delete the current broker configuration without a backup.
4. Run `EDGEQUANT-APP.bat`; open **Dashboard**. Both MT5 terminals must already be signed in and connected. Use **Brokers / MT5** to verify MAIN and EXTRA connection status and exact GOLD symbols.
5. Confirm the two Dashboard broker cards show **different broker login numbers and bid/ask quotes**, and compare their P&L with each MT5 terminal. Initially test on **demo accounts**.
6. If an account is OFF for *new trades*, it can still appear in this read-only dashboard if saved and connected. The existing ON/OFF trading controls are unchanged.

**No changes to:** order-routing engine, BUY +0.99 / SELL −0.90, two layers per entry, 50-pip quick TP, signal TP, SL offsets, Auto BE, LIMIT/STOP/first-touch MARKET logic or Telegram edit matching.

## Verification

- Offline Python tests: 140/140 pass (includes 6 new broker dashboard tests).
- Engine self-tests: 556/556 pass.
- Desktop legacy self-check: 321 pass / 3 existing failures, *identical to original input ZIP* (old UI/theme / 49-pip expectations).
- Dashboard cards rendered in an isolated virtual-display test with separate USD and USC examples.
- **Not verified against live Windows/AWS MetaTrader 5 terminals**. Validate on demo accounts before relying on values or enabling live trading.
