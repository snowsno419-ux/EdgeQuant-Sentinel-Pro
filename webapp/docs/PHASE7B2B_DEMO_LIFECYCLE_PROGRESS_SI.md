# EdgeQuant Sentinel Pro — Phase 7B2B DEMO Lifecycle (2026-11-08)

**Development status: Offline-tested; NOT production-ready.**

## Full source snapshot
The complete updated 111-file ZIP is in the ChatGPT conversation:
`EdgeQuant_Sentinel_Pro_Phase7B2B_Demo_Market_Position_Lifecycle_20261108.zip`
SHA256: `21f3d696f4fe525696909afc966cf83caaa779eb76edf6d7f15e4cd2279d93d3`.

**This GitHub branch is a partial milestone checkpoint, NOT a synchronized copy of all 111 ZIP files.** Source ZIP remains the complete snapshot. Original desktop main remains unchanged.

## Built in the complete ZIP
- `apps/api/src/copy_lifecycle_service.ts`: Receiver-controlled independent demo market/position opt-in; tenant/account-scoped authenticated one-use market/position claim and ACK; expired/ambiguous sends held for manual broker reconciliation.
- `apps/api/src/copy_lifecycle_core.mjs`: strict market, position, ACK, and lot/risk contract validation.
- `workers/windows/mt5_lifecycle_dispatch.py`: Windows worker claim -> independently guarded DEMO trade execution -> retry ACK only. No duplicate order_send on ACK failure.
- `workers/windows/mt5_provider_position_watcher.py`: provider read-only manual MARKET position SL/TP modify, deal-verified partial/full closes; stable SQLite outbox and no guessed close when position disappears.
- `apps/api/migrations/010_lifecycle_dispatch.sql`: additive indexes.
- Responsive Web/Mobile Copy Trading independent DEMO Market and Position ON/OFF controls. Default OFF.
- Strict Direct Copy original provider type, no Telegram BUY +0.99 / SELL -0.90 offset, no 2 layers. Telegram-only LIMIT→STOP fallback unchanged.

## Tests performed (offline only)
- Node domain 9/9
- Node API/security/policy 186/186
- Fake-MT5 Python/SQLite 189/189
- **384/384 offline tests passed**
- 20/20 TS/TSX source syntax-transpile checks passed
- ZIP integrity verified, 111 files.
- npm offline install failed ENOTCACHED for @fastify/cookie. Real Next/Fastify build, actual PostgreSQL migrations and Windows MT5 DEMO integration NOT VERIFIED.

## Safety + limits
Production mode always blocks DEMO dispatch. Opt-in has three layers: backend operator flags, receiver subscription settings, and Windows worker flags; broker account must be DEMO + hedging and match login/server. Prior broker send results with unknown outcomes remain UNKNOWN_RECONCILE and are NOT blindly resent.

This is not yet a completed live or commercial copy trading solution. Remaining: actual real Windows DEMO/PostgreSQL E2E; broker history + multiple deals; automatic receiver position refresh after partial close; phone-only managed worker provisioning; billing/licensing; risk/analytics and production security.

**DO NOT connect real-money clients or promote as live ready.**
