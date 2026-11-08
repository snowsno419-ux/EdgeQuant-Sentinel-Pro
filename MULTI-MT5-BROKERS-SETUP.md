# EdgeQuant Sentinel — MAIN + Multiple MT5 Brokers (Windows)

This update preserves the GOLD LIMIT VIP signal parser, follow-up update handling, and entry auto-modification in the user's source project.

## Add another account

1. Open and sign in to your existing **MAIN** MT5 terminal first. Keep it installed and logged in.
2. Install **a separate MT5 terminal instance / folder per additional broker**. The MT5 Python API communicates with one terminal at a time; EdgeQuant safely switches among them sequentially, not as independent parallel workers.
3. Start `EDGEQUANT-APP.bat` (or rebuild the Windows client), open **BROKERS / MT5**.
4. In **ADD / EDIT MT5 BROKER ACCOUNT** enter:
   - **ACCOUNT LABEL**: e.g., `EXNESS` or `ICMARKETS` (uppercase letters/digits/underscore; not MAIN).
   - **LOGIN ID**: your MT5 account number.
   - **BROKER SERVER**: exact server from MT5 (e.g., your own broker's Demo/Real server; don't guess).
   - **PASSWORD**: trading password, not a read-only investor password.
   - **SEPARATE MT5 TERMINAL**: browse to the other broker's `terminal64.exe`.
5. Press **SAVE / UPDATE BROKER**. New brokers are OFF by default.
6. Stop the engine; click **TEST** for that broker (read-only check) or **CHECK ALL ACCOUNTS NOW**. Confirm login/server/account and terminal path match.
7. Confirm risk and symbol (`XAUUSD`, `XAUUSDm`, etc.) in that broker's MT5 account, then **TURN ON** that account. With `SEND_TO_ALL_BROKERS=True`, ON accounts receive eligible new signals alongside MAIN. An OFF account gets NO new orders.
8. Start in **TEST RUN / DRY RUN** and check both terminals. Test real placements only on **demo** accounts before considering live use.

**Main remains in the account list** even if extra accounts are saved; it cannot be removed. You can edit or remove any extra user-saved broker without deleting MAIN. Removing an account does not close its actual MT5 positions/orders.

## Security & storage

- Broker account name, login number, server and terminal path are saved in `%LOCALAPPDATA%\EdgeQuant\edgequant_brokers.json` (or `%APPDATA%` fallback).
- Passwords are saved only in `%LOCALAPPDATA%\EdgeQuant\mt5_broker_passwords.dpapi`, encrypted using Windows CurrentUser DPAPI; no password is written to the JSON config or logs. It can only be unprotected by the same Windows user profile.
- An unreadable vault or missing terminal/login/server/password causes the extra account to be SKIPPED. It is never logged into the MAIN MT5 terminal.
- A broker selection is accepted only after its terminal path, login and server match the expected values. A failed extra account may not be retried on another account.
- MAIN's originally observed executable, login and server are anchored and verified when returning to MAIN.
- Automatic broker fallback was disabled (`BROKER_FALLBACK = False`) to avoid duplicate orders or routing a rejected broker trade into the wrong account.

## Limitations

- On one Python MT5 connection, multiple accounts are checked **sequentially**, not concurrently. A simultaneous-account execution architecture would require separate per-terminal processes and more extensive integration.
- Broker connections **were not tested against real Windows MT5 instances** in this environment. The new broker manager has offline mock tests; prior baseline signal-parser tests currently have 2 pre-existing expectation failures (REVIEW versus REJECTED for invalid pending orders).
- The source ZIP is not a new compiled Windows installer. Use the existing build scripts to compile on a supported Windows/Python runtime. No Windows 7 support is guaranteed (this project launcher uses Python 3.12 and depends on modern packages).
- Do not share ZIPs containing your own credentials or session files. Password vault files are not included in this release.
