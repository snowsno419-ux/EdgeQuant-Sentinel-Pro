# EdgeQuant client installer — current-release regression gate (6 Nov 2026)

## Screenshot error reproduced

`test_signal_format_examples.py:66` previously expected SL `4209.8`, but the product now deliberately preserves the signal SL `4210.0` for both pending layers; another test expected `4058.2` instead of `4058.0`. Both were legacy expectations contradicting the owner's latest shared-SL rule.

The original builder tested 29 Python unit tests then invoked `python edgequant_auto.py --selftest`. The latter is a large legacy internal suite that, in the current code, reports 510 passing + 46 failing expectations inherited from superseded behavior: modified signal SL offsets, MARKET-vs-LIMIT conversion, old pending validation, manual review fallback, older limits and stale-price rejection. These do not represent current owner-specified rules. The legacy self-test **has not been changed or made to pass**, and is still available to run separately for maintenance. Do not mistake its failure for a successful complete verification.

## New pre-build gate

`BUILD-CLIENT-INSTALLER-CORE.bat` now runs **all current Python unittest test_*.py tests** using `python -m unittest discover -s . -p "test_*.py" -v`, and checks syntax of the core engine, desktop, and VIP parser/update files via `python -m py_compile`. It does not disable testing or ignore failed unittest results. If either gate fails, build stops with error code 9. Full unittest suite: 197/197 passed in offline Linux workspace after aligning eight obsolete test assertions with the current rule. Several older test names remain historical, but their assertions now verify actual currently supported actions.

### Tests realigned to current behavior

- `test_signal_format_examples.py`: unchanged signal SL on each of two layers, BUY_LIMIT and SELL_LIMIT rather than stop conversions.
- `test_vip_entry_and_edits_v7.py`: direct BUY_LIMIT/SELL_LIMIT, unchanged signal SL.
- `test_gold_vip_market_touch.py`: direct pending order plans rather than retired WATCH_MARKET placement mechanism; separate first-touch helpers are still individually tested.
- `test_edgequant_vip_format.py`: preserve original signal text/SL for broker validation, rather than silently treating the message as unparseable.

### Distribution safety

No Telegram server, MT5 broker or live account was contacted by the tests. The generated ZIP is source and Windows build instructions, **not a tested Windows Setup.exe**. Installer compilation, MT5 native DLL import, source scrub, XLSX smoke test and Inno Setup packaging are still mandatory post-gate steps in the build script. Do not send a partial `dist` folder to clients, even when unit tests pass. Test with a DEMO MT5 account and clean Windows PC before distributing.

Run: `RUN-CLIENT-INSTALLER-KEEP-OPEN.bat` or `BUILD-CLIENT-INSTALLER.bat` after extracting to a simple writable path such as `C:\EdgeQuantBuild\`.

Troubleshooting: review `CLIENT-INSTALLER-BUILD.log`; do not post credentials, sessions or account tokens publicly.
