# Phase 7A — Direct MT5 Copy / Pending MODIFY + CANCEL (2026-11-08)

## Scope
**DEVELOPMENT DEMO ONLY. Not a production trading release.**

This branch is a **partial code checkpoint**; the 80-file complete Phase-7A source snapshot is provided separately in the ChatGPT conversation as:
`EdgeQuant_Sentinel_Pro_WebApp_Phase7_Pending_Modify_Cancel_20261108.zip`
SHA-256: `ca9e161e1cb8a40e815a01600f073cfe581a939329b2da2f8abd091f73344f02`

The full ZIP retains prior Phase1–6 source and adds:
- Provider Windows MT5 watcher checks broker order **history** before emitting CANCEL. FILLED -> FILLED_HOLD; no inferred cancellation or position close.
- New receiver follow-up API: `copy_followup_service.ts`, account-scoped mapping/worker/consent checks and one-time claim/ACK; broker history/reconciliation required for uncertain outcomes.
- Windows DEMO pending MODIFY/CANCEL executor: `mt5_demo_copy_followups.py`, original OPEN marker, receiver ticket, magic, exact account match, `order_check`, single broker send; if pending already filled, no action.
- `007_pending_lifecycle.sql`: original-open-delivery provenance, mapping status and execution indexes.
- API/agent routes and flag additions; Web/Mobile copy dashboard status text.
- Offline unit/mock tests for provider cancellation vs fill, pending modification, wrong account, wrong owner, unexpected responses and duplicate-send prevention.

## Default-off operator gates
- API: `PHASE4_ENABLE_DEMO_DISPATCH=1`, `PHASE6_ENABLE_DEMO_PENDING_COPY=1`, `PHASE7_ENABLE_DEMO_PENDING_FOLLOWUPS=1` only in non-production.
- Receiver Windows worker: `EDGEQUANT_ENABLE_DEMO_COPY_FOLLOWUPS=YES_I_ACCEPT_DEMO_FOLLOWUP_RISK`.
- Receiver subscription must already have explicit pending-copy opt-in.
- Always verify actual broker login/server, DEMO mode and original receiver pending order.

## Verification
- Node: **139/139 pass**.
- Python fake-MT5/SQLite: **91/91 pass**.
- Combined: **230/230 offline tests pass**.
- TypeScript/TSX transpile syntax: **17/17 pass**.
- **Not tested:** PostgreSQL migrations/E2E, actual native Windows MT5 demo broker, real broker modify/cancel acceptance, dependency installation/Next.js/Fastify production build, security and cloud deployment.

## Not implemented
Direct Provider market BUY/SELL order copying, pending→position ticket mapping, partial/full position closes, netting/hedging correctness and production multi-tenant cloud rollout. Existing Telegram offset/two-layer/LIMIT→STOP rules remain separate.

**GitHub this branch has core policy and migration only so far. Complete updated API + Python + UI source in the above ZIP is not yet fully synchronized.** Do not connect real-money customer accounts.
