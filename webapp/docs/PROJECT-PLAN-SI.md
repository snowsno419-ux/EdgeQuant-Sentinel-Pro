# EdgeQuant Sentinel Pro — Project Plan (සිංහල)

## Goal
Client PC නැති වුණත් phone එකෙන් provider follow කරලා Telegram signals හෝ Direct MT5 Copy Trading තෝරාගන්න පුළුවන් mobile-first SaaS. Cloud එකෙන් isolated managed Windows MT5 workers run කරනවා.

## Phases (no guaranteed timeline)
1. **P0** Desktop source audit, Master Prompt conflict resolution, credential scan, order-policy tests.
2. **P1** Receiver/Provider/Owner responsive UI, TypeScript API, PostgreSQL schema, secure identity + tenant permissions.
3. **P2** Telegram signal parser/replies, XAUUSD offset, 2-layer intents, duplicate locks and risk approvals.
4. **P3** Isolated Windows MT5 agent provisioning, broker connection, per-account reconciliation, restart recovery.
5. **P4** Direct MT5 copy trading watcher, order/position event mappings, modifications, partial/full close fan-out.
6. **P5** Smart Risk, expiry, Smart BE, partial TP, analytics, journals, exports and encrypted backup/restore.
7. **P6** Provider Marketplace, client licensing, subscriptions, mobile-only onboarding, Owner Admin monitoring.
8. **P7** Windows demo E2E, tenant/security/load testing, backups, recovery drills, monitored deployment and final release.

## Separate trading policies
**Telegram:** BUY +0.99 / SELL -0.90 (Gold only), 2 order layers per original entry, shared SL, layer1 configurable TP (50 pips default), layer2 signal TP or fallback; account+symbol+side+original entry+SL+TP identity.

**Direct MT5 copy:** Provider original order type/entry intent/SL/TP, configurable receiver lot size and risk. Do not apply Telegram offset or extra layer. Broker acceptance/fill/slippage varies per broker.

## Acceptance gates
- New Telegram repeated signal from different message id no duplicate in same MT5 account, restart recovery.
- Sender timeout → `UNKNOWN_RECONCILE`, no blind duplicate retry.
- Provider opens/edits/partially or fully closes → authorized mapped followers updated once.
- Auto BE OFF never changes SL; separate brokers don't leak data.
- Phone-only new account → managed Windows worker → demo MT5 trade with no client computer.
- License expiry blocks new orders but allows safe management of existing positions.
- Actual demo MT5 tests, security and backup restore required before production-ready label.

## Current status
Initial UI and pure trading-contract tests are a **prototype only**. AWS/other cloud choice, billing, domain and secure broker credentials require operator configuration and approved provider setup.
