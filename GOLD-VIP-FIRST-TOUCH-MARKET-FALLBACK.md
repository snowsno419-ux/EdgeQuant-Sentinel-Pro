# EdgeQuant Sentinel — GOLD LIMIT VIP First-Touch MARKET Fallback

**Source update, not a Windows installer. Demo MT5 verification is required.**

## Exact behavior

For `GOLD LIMIT VIP` **only**, each original entry keeps the existing GOLD adjustment: BUY `+0.99`, SELL `-0.90`. The application first tries a broker-valid LIMIT, then a broker-valid STOP at that **unchanged adjusted price**. If neither pending type is valid because the live price sits inside the broker's stop-distance band, it **does not immediately buy/sell at market**. Instead, it writes an exact-message, exact-broker, one-shot **virtual market watch** to the current Windows user's EdgeQuant local-data directory.

When the app is running, the watcher checks quotes about every 0.6 seconds; BUY uses **Ask**, SELL uses **Bid**. On the first *observed* quote at the adjusted entry (within **1 XAU pip = 0.10 price units** under the engine's Gold pip definition), it rechecks account identity, enabled broker/channel, emergency stop, daily-loss/risk guards, market open, spread, symbol, SL/TP validity, broker minimum stop distance, and the two-layer order cap. Then it durably claims the entry and attempts **two MARKET DEALs** once:

- **Layer 1:** fixed quick TP, normally **50 Gold pips** (= 5.00 price units using the existing pip table).
- **Layer 2:** original signal TP (including a valid Telegram edit received before the touch).
- **Both layers:** original signal SL with existing BUY `+0.20` / SELL `-0.20` protective price adjustment; same configured lot sizing.
- **Range signals:** each entry has its own independent two-layer pending-or-market-watch group; mixed STOP/LIMIT/virtual entry groups are supported.

If the broker definitively returns `10015 INVALID_PRICE` on both attempted pending layers *after* the planning preflight, a virtual watch is armed if the system has confirmed there is **no remaining accepted/uncertain pending order**. Broker `10016 INVALID_STOPS`, missing symbol, missing protection, and uncertain/partial execution never trigger a blind MARKET retry.

The first touch is based on **polled quotes**, not a tick-level guaranteed fill. A spike between polls can be missed; if the quote is too far from the entry, the system does not chase it. Quotes older than 15 seconds are ignored. Watches expire after **2 hours**, and are cancelled if the source channel or target broker is turned OFF. Closing EdgeQuant stops watching; persisted waiting records resume when it is reopened, provided they have not expired and safety settings still permit trading.

**One-shot protection:** the watcher creates an exclusive durable `.claim` marker before sending either MARKET order. A timeout/crash/uncertain broker outcome is never automatically replayed. Two market deals cannot be made atomic by the MT5 API: a broker may accept one and reject the other. An accepted market position is **not automatically closed** to simulate rollback. Check Trade History if an outcome is partial or uncertain.

**Telegram updates:** only the same original Telegram chat ID + message ID may modify a waiting entry. Edited original signals can update entry/SL/signal TP on the virtual records; direct-reply TP/SL updates, exact single-price entry updates, and `Don't enter` cancellation are supported with guardrails. Layer 1 quick TP is kept fixed. Ambiguous edits cancel/skip virtual entry records instead of speculatively trading.

## Files changed

- `edgequant_auto.py`: quote-side plan fallback, watcher persistence integration, async polling, broker-scoped risk/identity checks, edited-message linking and journaling.
- `edgequant_vip_market_touch.py`: independent persistence/claim helpers and pure quote + SL/TP validators.
- `test_gold_vip_market_touch.py`: offline watch, replay guard, edit, entry-level range, BUY/SELL quote and broker-definite rejection regression tests.
- `test_parallel_mt5.py`: adapt mock helper to accept the newly optional watch context.

## Verification and limitations

- Offline unit and engine self-tests are intended to run with `python -m unittest discover -p 'test_*.py' -q` and `python edgequant_auto.py --selftest`.
- **Not tested live** with a Windows MT5 terminal, Telegram channel, broker fills, or a Windows 7 installer.
- Market execution price, fills, slippage, gap behavior, and broker SL/TP acceptance cannot be guaranteed. This is not a promise of two confirmed orders or profitable trading.
- No forced market entry when STOP/LIMIT is still broker-valid. Only rejected quote-side cases are watched.

## Runtime data

Virtual queue is stored in `%LOCALAPPDATA%\\EdgeQuant\\gold_vip_market_touch\\` on Windows. The folder contains source message IDs, broker name/login/server (no passwords), adjusted entry, SL/TP, lots, watcher state, and durable one-shot claims. Avoid deleting claim records without reconciling broker history.
