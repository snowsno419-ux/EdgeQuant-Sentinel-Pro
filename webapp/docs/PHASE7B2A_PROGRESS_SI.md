# EdgeQuant Sentinel Pro — Phase 7B2A (2026-11-08)

**Status: Development source / offline DEMO prototype only. Not live, not production-ready.**

## Full source delivery
ChatGPT conversation ZIP:
`EdgeQuant_Sentinel_Pro_Phase7B2A_Market_Position_Foundation_20261108.zip`

ZIP includes 100 source/config/design/test files. ZIP integrity verified.
SHA-256: `5e7d57b52ffd0da23a5f0838b9dd432281a7afc0dfb45d41be190431c2902764`.

**This GitHub branch remains a PARTIAL milestone checkpoint, not an identical clone of the full ZIP.** New Python/TypeScript UI/API files are in the ZIP and still need synchronization. Original desktop `main` branch is unchanged.

## Added in full ZIP
- Read-only `mt5_provider_market_watcher.py`: new manual BUY/SELL OPEN events verified via order/deal + active hedging position; first-run baseline prevents old trades from unexpectedly copying; persistent SQLite outbox with deterministic IDs; does not publish provider position modify/close events yet.
- Standalone `mt5_demo_market_copy.py`: strict DEMO BUY/SELL broker request, FOK, fresh quote/spread/volume and SL/TP checks, broker order/deal/position post-verification. **Not auto-connected to claim/ACK**.
- Standalone `mt5_demo_position_lifecycle.py`: DEMO receiver original-order ownership verification and hedging-position SLTP, partial close/full close prototype. **Not auto-connected to claim/ACK**.
- `position_actions_core.mjs`: pure plans and tenant-scoped mapping validation; `copy_lifecycle_preview_service.ts`: RECEIVER-only read-only API, `/api/v1/copy/lifecycle-previews` GET.
- Responsive `/portal/copy-lifecycle` read-only event status UI; subscription permissions for future market/position copies default OFF (migration 009).

## Actual tests
- `npm test`: 9 Node domain + 157 Node API/security/policy = **166/166 passed**.
- `python -m unittest discover -s workers/windows -p 'test_*.py'`: **167/167 passed** using fake MT5/SQLite.
- **333/333 offline tests pass**.
- Syntax-only `typescript.transpileModule`: **20/20 TS/TSX files** no syntax diagnostics.
- Full npm/Next/Fastify builds, actual PostgreSQL migrations, native Windows MT5 DEMO, authenticated market/position copy claim/ACK, cloud deployment and security E2E **NOT VERIFIED**.

## Non-negotiable rules
- Telegram XAUUSD BUY +0.99 / SELL -0.90, 2 layers and Telegram-only LIMIT → STOP fallback remain unchanged.
- Direct MT5 copy uses provider's actual original order type. No Telegram offset/forced 2 layers.
- Never close provider ticket on receiver MT5: use only mapped receiver position ticket + identifier verified from actual broker history.
- HEDGING + native DEMO mode only for prototypes; netting and real accounts blocked. No uncertain resend.
- Market Execution mode may not honor requested `deviation`/price; never promise zero slippage.

## Next
Implement exact one-use authenticated market/position claim+ACK service, per-subscription explicit opt-ins, provider position modify/partial/full-close observation, PostgreSQL + Windows DEMO E2E; only then consider enabling supervised DEMO copying.
