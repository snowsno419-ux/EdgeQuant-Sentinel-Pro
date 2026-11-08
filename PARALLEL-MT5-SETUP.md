# EdgeQuant Sentinel — Parallel Multi-MT5 Execution (Source Update)

## What changed

When two or more enabled MT5 accounts are targeted by the same Telegram signal, the engine now launches a separate Python subprocess for **every targeted account at once** rather than switching the singleton MetaTrader5 Python connector sequentially. Each worker independently verifies its executable, MT5 login and exact broker server; resolves the exact configured broker symbol, checks fresh quotes/SL/TP/spread/account limits, builds the account-specific two-layer plan and submits to that account alone. The existing one-account execution path is preserved.

### Setup (Windows source version)

1. Extract the entire ZIP to a normal writable folder. Keep `edgequant_auto.py`, `edgequant_parallel_mt5.py`, `edgequant_desktop.py` and `EDGEQUANT-APP.bat` in the same folder.
2. Launch with `EDGEQUANT-APP.bat` using a working Windows Python installation with `MetaTrader5` installed (the existing launcher prefers Python 3.12).
3. Open your MAIN MT5 terminal and log into it as usual. MAIN path/login/server are detected and locked at dispatch time.
4. Install **a separate MT5 terminal executable** for each additional account. Under BROKERS/MT5 use Add/Edit: account label, Login ID, full Server name, Password, separate `terminal64.exe` path. Save, TEST, then ON. New accounts default to OFF.
5. Ensure `SEND_TO_ALL_BROKERS = True` and `BROKER_FALLBACK = False` in the engine settings (these are already the shipped defaults).
6. If a broker uses `XAUUSDm`, `XAUUSDc`, `GOLD` or another symbol, select the correct symbol mapping for that account.
7. Use DEMO ACCOUNTS first. Send one valid fresh Telegram signal and verify the orders and tickets **inside every individual MT5 terminal**.

### Important safeguards

- One subprocess per enabled broker is launched concurrently. Broker fill times and prices can still differ due to Python process startup, broker response, spreads, stops, and market conditions; this is **not** atomic exchange execution.
- No broker password is passed in process command arguments, job stdin JSON, or returned trade receipts. The worker uses the existing Windows DPAPI credential vault under the current Windows account.
- An account whose terminal/login/server identity does not match is SKIPPED, never silently attached to MAIN.
- A broker OFF or emergency-stop event blocks new orders. The existing account-specific money/spread/risk preflight and pending LIMIT checks remain active.
- Each worker persists an account+Telegram-message claim **before** order_send under `%LOCALAPPDATA%\EdgeQuant\parallel_mt5_claims`. If a worker returns an uncertain result or times out, it is **never automatically retried**. Verify the broker's actual MT5 history before making any manual adjustment. Do not bulk-delete claim files.
- Position-manager loops now select the appropriate broker per iteration rather than combining same-number tickets from unrelated accounts. Broker-scoped action metadata avoids some cross-broker ticket collisions.
- With only one enabled target, the original single-account execution code remains in use. Signal updates / follow-ups continue through the existing scoped management path; they are NOT parallelized in this release.
- This is a Python SOURCE ZIP. No Windows 7-compatible installer or PyInstaller executable is included or certified. It is not live-tested against a real MT5 terminal here.

### Offline test commands

```bat
python -m unittest -v test_parallel_mt5
python -m unittest discover -p "test_*.py" -q
```

Verification for this update: 11/11 parallel-specific tests passed; the entire 100-test suite passed 98 and reported the two pre-existing GOLD pending LIMIT test expectation failures from the input ZIP (the implementation rejects invalid orders; those tests expect review records). No live Windows/MT5 connection or simultaneous fills were verified here.

### Troubleshooting

- Only MAIN receives a trade: confirm extra brokers show ON, TEST passes, the server name is exact, and each broker has its own executable path. Check ACTIVITY for broker-specific skips.
- `uncertain`: check that broker's MT5 orders and deals/history; never blind re-run the same Telegram message.
- Broker symbol absent: set the correct XAUUSD/GOLD mapping under that broker.
- The extra broker terminal may take time to connect; a delayed/rejected fill is not proof of a parallel fan-out failure.
