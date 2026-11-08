# EdgeQuant Sentinel Pro — Phase 7B1 / Read-Only Pending-to-Position Reconciliation

**Status: DEVELOPMENT ONLY (2026-11-08). NOT production-ready.**

### Complete deliverable
Conversation attachment: `EdgeQuant_Sentinel_Pro_WebApp_Phase7B1_Readonly_Position_Reconciliation_20261108.zip`.

Verified ZIP: **88 files**, integrity check passed.
SHA-256: `741a636e8906ddb51cba71889388800e480012da9718858c87b26bf713b3a9ef`.

**GitHub branch is a PARTIAL milestone checkpoint**. The ZIP contains the complete updated Phase 7A → 7B1 source snapshot; the repository branch is not yet synchronized with all changed API, worker, tests and web UI source files.

### Implemented in full ZIP
- `workers/windows/mt5_position_reconciler.py`: read-only DEMO receiver reconciliation of original pending ticket via `history_orders_get(ticket=...)`, matching opening `history_deals_get` position ID and exact active `positions_get` hedging position. Original EdgeQuant magic/comment and broker account identity verified.
- Fail closed on netting, conflicting/multiple deals, wrong broker, missing history, unowned position and uncertain result.
- `008_position_observations.sql`: tenant-bound mapping evidence and audit history.
- `position_reconcile_service.ts`, `position_reconcile_core.mjs`: worker-authenticated, account-scoped report and job endpoints; conflicting mapping becomes `NEEDS_RECONCILE`.
- `/portal/copy-trading` shows receiver order → position evidence. **NO CLOSE/PARTIAL_CLOSE execution**.
- `mt5_heartbeat_agent.py` optional read-only cycle; OFF by default.
- Previous Telegram XAUUSD BUY +0.99 / SELL -0.90 two-layer and Telegram-only LIMIT→STOP safety; Direct MT5 copy order-type separation unchanged.

### Flags
API nonproduction: `PHASE7B_ENABLE_READONLY_RECONCILE=1`.
Windows receiver DEMO worker: `EDGEQUANT_ENABLE_READONLY_POSITION_RECONCILE=YES_READONLY_ONLY`.

The read-only worker has **NO order_send**, and is disabled by default. Existing demo order executor flags remain independently OFF.

### Validation
- Node domain and backend unit/mock tests: **152/152 pass**
- Python fake MetaTrader 5 tests: **108/108 pass**
- **260/260 offline tests pass**
- 18 TypeScript/TSX source files transpile syntax checks pass.
- `npm install --offline` failed: `ENOTCACHED` missing registry packages. Real Next/Fastify production build **not verified**.
- PostgreSQL migrations, Windows MT5 DEMO broker, cloud deployment, end-to-end trade copying and security audit **not verified**.

### Still required
Provider market BUY/SELL copy, real market order tickets/deals reconciliation, partial/full close execution, pending/position transitions on provider and receiver sides, netting/hedging E2E, cloud provision, billing/licenses, production hardening.

Do not connect real-money accounts or sell Phase 7B1 as completed trading platform.
