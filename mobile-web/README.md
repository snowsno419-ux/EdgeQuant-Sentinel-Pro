# EdgeQuant Sentinel Pro — Mobile + Web Cloud Integration (Phase 4.0)

**Status: read-only cloud API bridge published; database and MT5 worker NOT connected. No live trading.**

The Neon Dark Pro PC-style web UI runs on Vercel. It now calls same-origin /api/health every 30 seconds. Verified account logins can eventually read their own DEMO MT5 broker snapshots from /api/dashboard. Until PostgreSQL and a Windows DEMO worker are provisioned, the site deliberately displays **API ONLINE · DB OFF** and MT5 **OFFLINE**. It does not fabricate trading balances.

## Architecture
- mobile-web/index.html, styles.css, app.js — responsive public frontend. Browser draft settings do NOT change live trades
- mobile-web/api/health.js — cloud API reachability and configuration status
- mobile-web/api/login.js, me.js, dashboard.js — verified email + authenticator login, httpOnly cookie sessions and tenant-filtered read-only broker snapshots (fail closed without DB)
- mobile-web/api/worker-observation.js — Ed25519-verified DEMO account observations with replay/out-of-order protections (fail closed without DB)
- mobile-web/api/_lib — server-only helper modules, not public frontend content
- mobile-web/package.json — pinned PostgreSQL driver (pg)

A separate Windows DEMO-only read-only MT5 relay has been developed but is **NOT** installed, publicly deployed or connected. No broker passwords, Telegram OTP/session or worker private keys belong in this GitHub repository.

## Still required before real data
1. Provision managed, private PostgreSQL and apply reviewed database migration; configure DATABASE_URL as a **Vercel secret**, never as a public NEXT_PUBLIC variable
2. Securely provision verified user accounts + 2FA recovery, broker-account references and assigned worker Ed25519 public keys, with least privilege and audit
3. Run an isolated read-only worker with an already logged-in Windows MT5 DEMO terminal, confirm exact broker identity and timestamps
4. Test from Android and desktop with actual authenticated live broker observations, tenant boundaries and worker restarts

## Not available
No real Telegram integration, automated signal execution, BE/trailing/close, payments, Provider marketplace, 100-client workers, or live MT5 orders. Original Windows desktop trading logic is unchanged. Do not put real trading credentials into the public UI.

GitHub main branch auto-deploys to Vercel.