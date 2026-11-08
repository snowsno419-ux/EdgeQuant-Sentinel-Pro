# Phase 3 — MT5 Cloud Worker Pairing Milestone (2026-11-08)

මෙම branch එකේ Windows MT5 pairing හි **subset** (pairing validator, worker pairing database migration, Windows heartbeat prototype) commit කර ඇත. **මෙම GitHub branch එක තවම ZIP එකේ සම්පූර්ණ source snapshot එක සමඟ synchronize වී නැහැ.**

Full Phase-3 project ZIP was created in the ChatGPT conversation as:
`EdgeQuant_Sentinel_Pro_WebApp_Phase3_Mobile_MT5_Pairing_20261108.zip`.

## What's in the complete ZIP
- Previous responsive Web/Mobile UI, login/verify and tenant-scoped broker registration
- User-generated one-time pairing token / revoke controls
- Worker claim and authenticated heartbeat API endpoints
- PostgreSQL migration `002_worker_pairing.sql`
- Windows real-MT5 connectivity-only Python worker, per-account Windows DPAPI token storage
- Error on wrong broker identity; computed DISCONNECTED after 120 seconds without heartbeat
- Sinhala setup instructions and tests (offline 35/35 pass: domain 9; backend 21; Python 5)

## Critical limitations
- Windows MetaTrader5 demo-server connection, PostgreSQL integration and Next.js/Fastify production builds NOT YET VERIFIED.
- The Windows heartbeat agent **DOES NOT PLACE TRADES**; there is no live order executor.
- Automatic Windows cloud worker provisioning, Telegram and Direct MT5 order fan-out, licensing and production auth hardening remain incomplete.
- DO NOT deploy to live customer accounts or advertise this as a production trading app.

## Next
Complete GitHub code sync; run actual frontend/backend build and PostgreSQL E2E; then Windows demo MT5 authentication, reconciliation and worker deployment.
