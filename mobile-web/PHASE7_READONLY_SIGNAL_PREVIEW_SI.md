# EdgeQuant Web/Mobile — Phase 7 staged source (2026-11-17)

Desktop reference: EdgeQuant Sentinel Pro v2.0.4 FULL_SOURCE_LOGO_FIXED_20261117.zip. The Windows desktop remains separate from cloud source and is not deployed into Vercel.

## Added
- Authenticated account-scoped Telegram inbox includes a non-executable signal_preview for each message/revision.
- Narrow English GOLD/XAUUSD BUY/SELL parsing projects two layers per entry, with +50 Gold pips on Layer 1 (0.1 price per project pip), original Telegram TP on Layer 2 and shared SL. TP3 is prioritized if present.
- Channel page displays READ-ONLY / NOT SENT and projected entries, TP and SL.
- Malformed/management/ambiguous messages are UNPARSED and are never trade requests.
- No STOP pricing without fresh verified MT5 worker Bid/Ask and broker tick/stops metadata.

## Not included
- Full desktop parser parity, Sinhala/Singlish, edits/replies correlation, defaults, execution and broker-day reset.
- Hosted MT5 worker, personal Telegram phone OTP/2FA, paid runtime, and production rollout.
- This branch does not enable live trading or issue orders.

## Test
node --test cloud-tests/test_phase7_signal_preview.js

Live auto-trading remains OFF. Broker DEMO end-to-end validation is required before trading is implemented.
