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

## Phase 7B — actual connection readiness and operator setup
- The authenticated /api/dashboard response includes per-user Telegram listener heartbeat, selected-channel count and DEMO worker status. It never treats metadata alone as a connected MT5 terminal.
- Web Dashboard shows next steps for Telegram listener provisioning, selecting monitored groups, DEMO broker registration, pairing and starting the worker.
- The DEMO-only worker refuses to report fake online status when terminal_info.connected is false or positions_get/orders_get fails.
- CI workflow .github/workflows/phase7-readonly-ci.yml runs Node regression and isolated Python worker tests; no MetaTrader5 terminal or live orders.
- Web source is staged in a draft PR. Do not mark real users CONNECTED based only on PENDING or APPROVED requests.

## To bring up an actual read-only DEMO connection
1. Verify your Neon migrations and Vercel production environment privately. Never publish database URL, Telegram API hash, session files, broker credentials, one-use tokens or Ed25519 private keys.
2. Telegram: the verified account requests a personal listener in Channels. Operator provisions an isolated private host, does user-consented private Telethon login (not a public phone OTP form), and authorizes its **public key only** for that user. Launch monitor and wait for a fresh signed heartbeat. Then the logged-in user enables their discovered channels.
3. MT5: the verified account registers a DEMO broker with exact account and server in Brokers. On a separately hosted secured Windows DEMO terminal, run edgequant_demo_worker.py pair with the 15-minute token. Owner checks matching public-key fingerprint and approves. Start observe with exact broker ID, DEMO login and server. Do not input MT5 passwords in the web UI.
4. Check the dashboard says signed read-only ONLINE only when the authenticated worker is fresh, then confirm a permitted Telegram message reaches inbox and a DEMO signed broker observation shows balance/equity.
5. No live orders, private user OTP self-service or production auto execution are introduced in this phase. Hosting and account authorization must be explicitly configured and validated separately. A hosted 24/7 MT5 terminal is not provided by Vercel.

Local checks (before release):
```sh
npm install --prefix mobile-web
node --test cloud-tests/test_*.js
python -m pip install cryptography
python -m unittest discover -s cloud-tests -p 'test_phase7_*.py' -v
```
