# EdgeQuant Sentinel Pro — Phase 6 / Pending MT5 Demo Copy

**Status: DEVELOPMENT / DEMO ONLY — NOT PRODUCTION READY**

## Full source snapshot
Download the conversation attachment:
`EdgeQuant_Sentinel_Pro_WebApp_Phase6_Pending_Demo_Copy_20261108.zip`
(71 source/config/test/design files; ZIP integrity verified).

This GitHub milestone branch is **NOT YET synchronized with every file in that ZIP**.
The complete Phase 6 code is in the archive; this branch currently records the migration and checkpoint.

## New functionality in full Phase 6 archive
- Provider Windows MT5 DEMO account **read-only** pending watcher:
  - Detects **new manually placed** BUY/SELL LIMIT/STOP pending orders and Entry/SL/TP edits.
  - Uses persistent per-service SQLite outbox and deterministic event revisions; survives agent restarts.
  - On initial connect, preexisting orders are baseline-only; no surprise copy; stale orders are skipped.
  - Does not treat disappearing pending orders as cancels because they may have filled.
  - Ignores EA/EdgeQuant-originated orders to reduce circular copying risks.
- Receiver Windows MT5 DEMO **pending OPEN only** executor:
  - Keeps provider original pending order type, entry, SL/TP and receiver's lot policy.
  - Rejects invalid broker quote geometry, volume/tick precision, unsupported symbol/type and order_check failures rather than repricing or changing types.
  - Tries to reconcile broker history/orders/positions before a single send, no automatic blind retry.
- Backend:
  - Receiver opt-in per subscribed broker account DEFAULT OFF.
  - Verified DEMO worker required; lease identity bound to receiver broker/tenant, one attempt only.
  - Encrypted-hash lease verification, ticket ACK mapping, UNKNOWN_RECONCILE on ambiguous outcomes.
  - Stale provider events skipped, newer provider revisions block late stale OPEN.
  - **Production mode unconditionally disables demo dispatch.**
- Web/mobile Copy Trading page adds explicit DEMO Pending Copy enable/disable control.
- Existing Telegram +0.99/-0.90, 2 layers, and Telegram-only LIMIT→STOP fallback remain separate from Direct MT5 Copy.

## Test results
- Node domain/API security and policy: **124 / 124 passed**.
- Python Windows MT5 mock test suite: **69 / 69 passed**.
- Total offline: **193 / 193 passed**.
- TypeScript/TSX transpile-only syntax check: **16 files passed** (NOT a real production build).
- PostgreSQL migration apply, Windows native MT5 DEMO broker execution, Next.js/Fastify production build, cloud worker deployment, tenant E2E: **NOT VERIFIED**.

## Explicit opt-ins to test on demo only
- API non-production: `PHASE4_ENABLE_DEMO_DISPATCH=1` and `PHASE6_ENABLE_DEMO_PENDING_COPY=1`.
- Provider Windows MT5 worker: `EDGEQUANT_ENABLE_DEMO_PROVIDER_WATCH=YES_I_ACCEPT_DEMO_PROVIDER_WATCH` and `EDGEQUANT_PROVIDER_SERVICE_ID=<UUID>`.
- Receiver Windows MT5 worker: `EDGEQUANT_ENABLE_DEMO_COPY_PENDING=YES_I_ACCEPT_DEMO_COPY_RISK`.
- Receiver also separately enables DEMO pending copy for their subscription on Web Portal.

## Not yet implemented
- Provider market BUY/SELL and STOP_LIMIT copying, automatic receiver MODIFY/CANCEL/CLOSE/PARTIAL_CLOSE execution,
  broker pending→filled reconciliation, managed Windows cloud provisioning, billing, and production authentication audit.
- Never connect live customer accounts until integration tests and security validation are complete.

The project remains an iterative implementation. Do not claim all trades are copied or commercially ready.
