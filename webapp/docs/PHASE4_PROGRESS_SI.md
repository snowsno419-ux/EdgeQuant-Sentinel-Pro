# Phase 4 — Durable Demo Execution Foundation (2026-11-08)

**STATUS: Development / not production ready.** This is a deliberately safe intermediate milestone. Existing desktop code and repository `main` are unchanged.

## Complete Phase-4 deliverable in the ChatGPT conversation
`EdgeQuant_Sentinel_Pro_WebApp_Phase4_Demo_Execution_Foundation_20261108.zip`

The ZIP contains 52 source/config/design/test files, including all prior Phase-3 code, the new Phase-4 code and a Sinhala README. GitHub remains a **partial milestone branch** until the full source ZIP contents are uploaded or synchronized.

### Implemented in the full ZIP
- `apps/api/migrations/003_execution_intents.sql`: PostgreSQL tenant-scoped durable intents, 2 independent order legs, broker tickets and execution audit trail.
- `apps/api/src/execution_core.mjs`, `execution_service.ts`: account-scoped duplicates; demo-only stage, explicit approval, single-use worker lease, accepted/rejected/unknown statuses.
- `apps/api/src/index.ts`: authenticated preview, stage, list and demo approval REST endpoints plus worker claim/ack endpoints.
- `workers/windows/mt5_demo_executor.py`: strict DEMO account native MT5 check, account/server verification, exact LIMIT entry/SL/TP planning and broker-order recognition before submission; never blindly retries unknown sends.
- `workers/windows/mt5_heartbeat_agent.py`: native MT5 tradeMode heartbeat and optional independent demo executor.
- `apps/web/app/portal/trade-preview/page.tsx`: responsive receiver signal preview, staging, ledger and explicit demo approval UI.
- Pure policy rule isolation preserved: Telegram XAUUSD BUY +0.99 / SELL −0.90 and 2 layers; Direct MT5 copy does not inherit Telegram offsets/layers.

## Actual verification
- 9 existing trading-domain Node tests + 49 backend security/intent tests + 19 mock MT5 Python tests = **77/77 offline tests passed**.
- 13 TypeScript/TSX files transpiled without syntax errors.
- `npm install` timed out due registry access. PostgreSQL integration, API/Next.js production build, real Windows/demo MT5 submission and deployment **NOT VERIFIED**.
- There is no real Telegram ingestion/fanout or production Provider→Receiver Direct MT5 copy trading in this milestone.

## Safety
Demo dispatch OFF by default. In non-production only, all three independent opt-ins are required:
- API manual staging: `PHASE4_ENABLE_MANUAL_DEMO_STAGING=1`
- API demo dispatch: `PHASE4_ENABLE_DEMO_DISPATCH=1`
- Isolated Windows worker: `EDGEQUANT_ENABLE_DEMO_LIMIT_EXECUTION=YES_I_ACCEPT_DEMO_RISK`

The worker itself verifies native `ACCOUNT_TRADE_MODE_DEMO` prior to each broker submission and blocks REAL/CONTEST accounts. Do **not** use real-money client accounts or sell as finished software at this stage.

## Next steps
1. Sync all ZIP source files into GitHub; install dependencies and run build, PostgreSQL migrations and tenant-isolation E2E.
2. Execute controlled Windows MT5 DEMO tests with broker rejection and crash/reconciliation cases.
3. Add signed and authorized Telegram source ingestion; Provider subscriptions; Direct MT5 copy modification/close fan-out; risk manager; cloud orchestration and licensing.
