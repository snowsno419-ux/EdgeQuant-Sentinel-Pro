# EdgeQuant Sentinel — Universal Engine Development Update

**Package status: source development build; not a production-certified installer.**

## Implemented in this update

- XAUUSD LIMIT BUY entry uses the original signal entry + 0.99 price units.
- XAUUSD LIMIT SELL entry uses the original signal entry - 0.90 price units.
- Layer 1 default target is 49.90 Gold pips (Gold pip convention: 0.1 price units).
- XAUUSD LIMIT Layer 2 keeps the original signal TP; both layers keep the original signal SL.
- Two-price range signals preserve two entries × two layers = four intended orders. If a level or signal protection is invalid, both layers for the affected entry are routed to review instead of being silently dropped.
- Existing market-order entry path is preserved; market Layer 1 uses the new 49.90-pip setting as configured.
- Live MT5 spread is read from Bid/Ask and displayed on the Dashboard with detected broker, symbol, Bid/Ask, update time, and configured maximum spread.
- Spread threshold can be changed from the Dashboard. XAUUSD spread is shown in pips, where one pip is 0.1 price units. A value of 0 disables the spread guard.
- If a XAUUSD LIMIT entry is invalid against the live quote but the exact same price is valid as a STOP order, it is automatically converted to BUY STOP / SELL STOP and submitted without changing entry, SL, or TP.
- The executor rechecks the live quote immediately before sending and can convert a LIMIT to STOP if the quote moved after planning. If neither LIMIT nor STOP can legally use the exact entry price, the order is rejected with a clear log message rather than placed in Manual Review or silently repriced.
- High-spread orders and SL/TP or broker-specification failures still use the existing safety review/rejection behavior; this change does not bypass spread guards or alter SL/TP.
- The queue supports explicit Reject or Revalidate & Execute. Execution rechecks live quote, spread, entry direction, tick size, and SL/TP distances; it does not silently reprice the order. Uncertain broker results are not automatically retried.
- Telegram Studio supports joining a private group via its `t.me/+...` invite link and adding it to the destination list.
- Private basic groups and private supergroups post as the signed-in account without a channel-style Send As override. Public channels and public supergroups retain explicit destination Send As checks.
- Timestamped source backups were created before modifications.

## Validation performed in this environment

- Python compilation: passed.
- `python -m pytest -q --disable-warnings`: **59 passed, 11 subtests passed** after the STOP-conversion change.
- `python edgequant_auto.py --selftest`: **555 passed, 0 failed** after the STOP-conversion change.
- `python edgequant_desktop.py --selfcheck`: **324 passed, 0 failed**.
- `python edgequant_check.py`: source/build-kit checks passed; the checker reports MT5 and Telethon are not installed in this environment.
- `python edgequant_desktop.py --xlsx-selfcheck`: passed.

## Not yet verified

- No live Telegram login, private-group join, or actual Telegram post was performed here.
- No MT5 terminal/broker was connected; live broker execution and demo-account order placement were not tested.
- The MetaTrader5 Python package and Telethon are unavailable in this build environment, so the MT5 import self-check cannot pass here.
- Windows EXE / Inno Setup installer was not built or smoke-tested. This environment is not a Windows build machine and PyInstaller is not installed.
- A clean Windows 10/11 installation test remains a release gate.

## Private group requirements

The app cannot bypass Telegram's membership, invite approval, bans, or posting permissions. The connected Telegram account must be able to join and send messages in the selected group. If Telegram sends a join request, an admin must approve it. Broadcast channels still require Telegram to authorize the selected Send As identity.

## Before real-money use

Run `TEST RUN` first, then verify the dashboard and Manual Review behavior on an MT5 demo account. Do not enable live trading until the Windows installer and broker-specific order behavior have been tested on a clean machine.
