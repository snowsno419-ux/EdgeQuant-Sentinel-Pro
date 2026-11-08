# EdgeQuant — Duplicate Entry Protection (7 November 2026)

## Owner's rule
For a **new Telegram placement signal**, do not place the same entry again when the **same MT5 account**, **symbol**, **BUY/SELL direction**, **original signal entry**, **SL**, and **signal TP** match a previously submitted entry. The protection works across different Telegram message IDs, channels, reconnects, app restarts, and concurrent broker workers.

Example:
- `GOLD BUY 4000 SL 3950 TP 4100` → eligible on the first arrival, so the normal two-layer plan may be submitted.
- A **different Telegram message** with `GOLD BUY 4000 SL 3950 TP 4100` → **DUPLICATE ENTRY**, neither layer is resubmitted to an account that has already attempted it.
- `GOLD BUY 4000 SL 3950 TP 4110` → a changed signal TP; it is **not an identical tuple**. If it is an *edit/reply* to the original signal, the Telegram update handler should modify the original orders rather than create new ones.

**Important implementation details**
- Compare original signal entry, not Bid/Ask, and use the *Layer-2* signal/fallback TP for the identity. Layer-1's configurable quick TP is deliberately ignored for duplicate identity. Broker-specific symbol suffixes, e.g. `XAUUSDm`, normalize to `XAUUSD`.
- Entries are deduplicated **individually**. If a range contains one previously submitted entry and one new one, only the new entry gets its usual two layers.
- Separate MT5 accounts (different login or server) have their own independent protection. Changing the broker display name does not bypass it on the same account.
- This is **not** a market-price validity check, a size limit, or a restriction on Telegram edit/management messages. No Bid/Ask comparison is used to decide whether an entry is a duplicate.
- Active EdgeQuant MT5 orders/positions are inspected too, to catch currently active duplicates from older versions. However, **old closed trades from versions without account-linked receipts cannot always be matched safely**; verify the old MT5 order/history state before first deployment.
- Before broker submission, an exclusive filesystem receipt is atomically written in `%LOCALAPPDATA%\EdgeQuant\duplicate_signal_claims_v1\` on Windows. The receipt remains after a crash or an uncertain order result: no blind repeat submission. Even definitive rejected attempts remain fenced by default; check MT5 history before choosing to reset one. Do **not** delete the entire directory casually.
- If identity is not verified, active broker orders cannot be read, or persistent claim creation fails, the app **fails closed** for that entry; it never turns off this duplicate guard to force an order.
- A broker can still reject an otherwise nonduplicate LIMIT order. This rule neither overrides broker prices/stops nor guarantees a fill.
- Rebuilding and installing the client with the new ZIP is necessary; changing the ZIP alone does not update the old installed EXE.

## Test and install
1. Stop the currently running EdgeQuant client. Back up your project/configuration and journal; do not copy secrets into a shared package.
2. Extract **this full ZIP** into a new build folder; do not merge it with an older source folder.
3. Run `RUN-CURRENT-RELEASE-TESTS.bat` for offline regression verification; or directly run `python -m unittest test_duplicate_entry_guard_20261107 test_parallel_mt5 -v` using the build Python.
4. Run `RUN-CLIENT-INSTALLER-KEEP-OPEN.bat` and install the newly generated `dist\EdgeQuant-Sentinel-Client-Setup.exe` after stopping the old app.
5. On an **MT5 DEMO** account, send a test signal, then send the same entry/SL/TP in a *different* Telegram message. Confirm that the app logs `DUPLICATE ENTRY` and MT5 receives no further pending orders.

Offline tests are not a live MT5 broker/AWS or Windows installer end-to-end test. Do not distribute to clients before completing those checks.
