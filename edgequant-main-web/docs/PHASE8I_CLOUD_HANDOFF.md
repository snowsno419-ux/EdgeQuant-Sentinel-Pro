# Phase 8I — Cloud API / Windows MT5 DEMO pairing handoff (2026-11-09)

This repository's public `edgequant-main-web` website remains a **static simulator**. It is **not** the private backend or an MT5 execution host.

Phase 8I source development has been packaged separately (not uploaded to this public GitHub repository). The changes include:

- Private Fastify API cloud environment preflight and DB-backed readiness status
- Docker/Caddy HTTPS deployment template for a private API VM with separately managed PostgreSQL and SMTP
- Windows-native MT5 read-only pairing preflight and an operator-side PowerShell setup helper
- Fail-closed production startup when credentials are missing/placeholders or DEMO execution flags are set
- Node 274/274, Python Windows mock 226/226 and Telegram bridge mock 11/11 tests passing

**Not deployed or verified:** private API, database migration, SMTP email delivery, Caddy TLS, native Windows MetaTrader5 pairing, real broker P&L, and Telegram-to-MT5 end-to-end limit-block tests. No funded broker execution is authorized.

## Next prerequisites

Provision a private PostgreSQL 16 service, verified email provider, public HTTPS API DNS, isolated Linux API VM, and persistent Windows DEMO MT5 VM. Store secrets only in private server/provider stores. Do not expose Telegram sessions, API hashes, MT5 passwords or worker credentials in this public repository or browser bundles.

The canonical public UI is unchanged until real private staging is verified. Link the Vercel project's GitHub Login Connection separately to enable push-triggered deploys.

The Phase 8I full ZIP and detailed Sinhala setup runbook were delivered in the conversation.
