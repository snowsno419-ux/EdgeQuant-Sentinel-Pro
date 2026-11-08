# EdgeQuant Sentinel Pro — Phase 5: Provider → Receiver Copy Trading Staging

**Status (2026-11-08): DEVELOPMENT ONLY. NOT LIVE COPY TRADING OR PRODUCTION-READY.**

## Full updated source snapshot
The **complete 61-file Phase-5 source archive** is provided in the ChatGPT conversation as:
`EdgeQuant_Sentinel_Pro_WebApp_Phase5_Provider_Copy_Staging_20261108.zip`.

This GitHub development branch is a **partial milestone checkpoint** and **has not yet been synchronized with every file in the ZIP**. Existing desktop `main` source remains untouched.

## Implemented in the full ZIP
- Provider role creates draft service for their MT5 account and can activate only when associated Windows provider DEMO heartbeat is verified.
- Receiver role selects an ACTIVE Provider service, grants explicit opt-in consent, selects their own broker account, and configures SAME/FIXED/MULTIPLIER lot policy with hard maximum. Can pause further events.
- Provider DEMO worker account-scoped authenticated API accepts OPEN, MODIFY, PARTIAL_CLOSE, CLOSE and CANCEL events.
- PostgreSQL migration `005_provider_copy_events.sql`: provider services, consented subscriptions, event ledger, original-to-receiver ticket mappings, staged delivery intents.
- Duplicate event id+payload-fingerprint rejection; strict incremental order revision; tenant and broker checks; follow-up requests never use a provider ticket to modify/close receiver trades.
- Responsive `/portal/copy-trading` Provider/Receiver page with real API-backed status.
- **No COPY delivery dispatch / claim endpoint exists.** Ledger rows remain STAGED, WAITING_TICKET_MAPPING or BLOCKED_RISK.
- Telegram XAUUSD +0.99/-0.90 two-layer and safe LIMIT→STOP policies unchanged. Direct MT5 copy always keeps provider original order type/SL/TP (no Telegram offset or forced two layers).

## Test report
- Node trading domain: 9/9 pass.
- Node backend/security/copy policy: 98/98 pass.
- Fake MT5 Python: 37/37 pass.
- Total **144/144 offline tests pass**, TypeScript 15 source transpile syntax check pass.
- npm install timed out; actual Next.js/Fastify production builds, PostgreSQL migration/E2E, Windows real DEMO MT5, cloud deployment **NOT VERIFIED**.

## Still required for real copy
- Windows provider MT5 watcher (orders/positions/history with reconciliation; prevent pending→filled double copying)
- Authorized receiver DEMO executor and ticket mapping acknowledgements
- Risk manager + broker contract/volume/symbol checks and market-order slippage handling
- Correct partial/full close, netting/hedging, revocation/reconnect, duplicate and cross-source collision tests
- Real PostgreSQL integration, cloud worker provisioning, E2E tests, production security

Never enable customers' live trading on this milestone.