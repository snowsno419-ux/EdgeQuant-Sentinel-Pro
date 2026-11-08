# EdgeQuant Sentinel Pro — Web Application Phase 1

**STATUS: DEVELOPMENT STARTED, NOT LIVE / NOT PRODUCTION READY.**

The current desktop source remains untouched in the repository root. The new multi-tenant cloud Web App is being developed separately under `webapp/`.

## Target
- Next.js responsive Receiver, Provider and Owner UI, original cyan/navy EQ brand.
- TypeScript API, PostgreSQL, Redis queue, tenant isolation and secure authentication.
- PC-free mobile-only clients with isolated managed Windows/MT5 cloud workers.
- Telegram signal execution and Direct Provider-MT5-to-Receiver-MT5 copy trading are separate modes.
- Real order execution must only start after authorization, risk/duplicate checks, and Windows demo MT5 verification.

## Rules (non-negotiable)
- Telegram XAUUSD BUY +0.99; SELL -0.90, two independent layers, common SL; TP1 configurable / TP2 signal or fallback.
- Direct MT5 copy: provider exact order type and intended entry/SL/TP with receiver lot policy; **NO Telegram offset or forced two layers**.
- Only account-scoped durable broker reconciling prevents duplicate execution; order-intent tests alone are not live execution tests.

## Current checkpoint
Phase-1 UI preview, minimal health API, pure order policy prototype; no live MT5 credentials, no actual worker provisioning, no production authentication or billing. See `webapp/docs/PROJECT-PLAN-SI.md`.

## Safety
Do NOT store MT5 passwords, Telegram sessions, client data, API keys or `.env` in GitHub. All sample balances/prices in design are fictitious.
