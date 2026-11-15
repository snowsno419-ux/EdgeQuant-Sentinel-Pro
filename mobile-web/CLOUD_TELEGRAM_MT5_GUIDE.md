# EdgeQuant Sentinel Pro — Telegram + MT5 Cloud Connection / DEMO

**Status: source implemented, cloud services not provisioned. Trading OFF.**

## 1. Telegram Bot mode — authorized channels only

This Bot API route is **not** Telegram phone-number login. It can receive new and edited messages from a Telegram group/channel only after the platform Bot is explicitly added there and given required read access.

Operator setup (do not share any token in ChatGPT, screenshots, or public GitHub):

- Create an EdgeQuant bot through @BotFather in Telegram.
- In Vercel `edgequant-mobile-web` → Settings → Environment Variables (Production, encrypted), add `EQ_TELEGRAM_BOT_ENABLED=1`, `EQ_TELEGRAM_BOT_TOKEN` (BotFather token), and `EQ_TELEGRAM_BOT_WEBHOOK_SECRET` (random 32–64 character A-Z/a-z/0-9/_/- secret).
- Redeploy Production to load the new environment variables.
- Sign in with the account authorized as Bot operator. While `EQ_SIGNUP_TEST_ONLY=1`, only `EQ_TEST_EMAIL` may initialize the Bot. Once public registration is configured, set `EQ_BOT_OPERATOR_EMAIL` to a separately authorized account.
- In Channels → CHECK BOT STATUS → INITIALIZE BOT WEBHOOK. Server configures the secret-protected webhook at `/api/telegram-bot-webhook` and enables only `message`, `edited_message`, `channel_post`, `edited_channel_post` updates.

Chat owner setup:

- Add the platform Bot to a channel/group with required Telegram permissions. For channel posts, add as admin. For group content, Bot privacy must permit reading signal posts; being an admin usually provides required access.
- In a group, an administrator posts `/eqid`; the Bot replies with the numeric chat ID. Record it in EdgeQuant Channels. Other groups/channels must be authorized separately.
- Register that numeric chat ID, label and LIMIT/MARKET type. The source starts OFF.
- Tap VERIFY ADMIN ACCESS; paste the one-time `EQVERIFY-...` code as admin in that same chat within 15 minutes, refresh and tap ENABLE READ-ONLY.
- New/edited text messages then appear in the read-only Telegram inbox; duplicate updates are ignored. **No trades are opened.**

Limitations: A Bot cannot log in to a person's Telegram account, discover all private groups, or access channels where it has not been added. Full Telegram MTProto user-account/OTP/2FA service needs a separately provisioned Linux cloud listener with strict session encryption and account isolation.

## 2. MT5 signed Windows DEMO worker pairing

Vercel Functions do **not** run `terminal64.exe`; clients without a PC require an isolated, remotely hosted Windows MT5 terminal. This change does **not** buy, deploy or start Windows hosting.

- On EdgeQuant Brokers / MT5 page, register exact **DEMO** broker name, server and account number (no password).
- Request a managed worker or arrange a trusted cloud Windows VM with MT5 terminal installed and logged into the matching demo account.
- Tap GENERATE PAIRING TOKEN. The one-use token is valid 15 minutes; keep it private.
- On the Windows worker, install Python 3.11+, MetaTrader5 and cryptography. Use `cloud-worker/edgequant_demo_worker.py` from the repository. `py edgequant_demo_worker.py pair` prompts for the token on the worker machine.
- The worker displays an Ed25519 public-key fingerprint. On the phone, tap CHECK PAIR STATUS. If the fingerprint matches, tap APPROVE READ-ONLY WORKER.
- On the worker run `py edgequant_demo_worker.py observe --broker-id YOUR_BROKER_ID --server YOUR_DEMO_SERVER --login YOUR_DEMO_ACCOUNT`. Use `--terminal` if several MT5 terminals are installed.
- When valid signed telemetry arrives within the freshness window, the Dashboard shows DEMO CONNECTED and live read-only balance/equity/floating P&L. No order execution is installed.

Never enter your MT5 password into EdgeQuant's public web pages, share pairing tokens in screenshots, or copy private Ed25519 keys into other clients' workers. The Windows worker machine requires hardened access controls. This is NOT a live trading setup.

## Deployment and schema

- `cloud-db/0007_telegram_bot_sources.sql`: verified chat claims, fresh Bot update replay guard and observed timestamps.
- `cloud-db/0008_mt5_worker_pairing.sql`: short-lived pairing state and claimed Ed25519 public key.
- No additional Vercel serverless functions: Telegram uses `api/telegram.js` and pairing uses existing `api/brokers.js`.
- DB retention must delete expired claims, pairings, old Bot update ids, stale sessions and event ids on an operator-maintained cadence.
- Bot and MT5 connections remain OFF until user-owned Bot credentials and a hosted Windows DEMO terminal are actually available. Do not claim a connection based on metadata or a pairing request alone.
