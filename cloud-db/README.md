# EdgeQuant Cloud — private PostgreSQL (not provisioned yet)

**The public GitHub repository and Vercel deployment contain NO DATABASE_URL or secrets.**

Provision a private managed PostgreSQL database (e.g. Neon free development tier, subject to provider limits). In the Vercel project `edgequant-mobile-web`, connect the database ONLY to the Production environment, using the provider's dashboard authorization. Do not paste connection strings into GitHub, public issues, chats, or front-end variables.

As the database owner in your provider's **private SQL Editor**, execute migrations **in order**:

1. `0001_readonly_schema.sql` (users, sessions, broker accounts, read-only MT5 worker keys/snapshots)
2. `0002_onboarding.sql` (one-time email verification, TOTP enrollment, throttling)
3. `0003_telegram_inbox.sql` (user-scoped signed Telegram inbox)
4. `0004_worker_requests.sql` (user's request for separate DEMO Windows worker)
5. `0005_password_reset.sql` (single-use, 20-minute account password recovery tokens)
6. `0006_telegram_listener_requests.sql` (user-initiated Telegram listener provisioning requests; no credentials)
7. `0007_telegram_bot_sources.sql` (one-time channel admin proof, replay safety and source verification)
8. `0008_mt5_worker_pairing.sql` (one-time DEMO cloud worker public-key pairing)

Prefer a separate least-privilege database role for Vercel API with DML grants only; never use the database owner as a public application credential. Restrict network access where supported, use TLS, backup/restore drills, and a scheduled retention job to delete expired verification/session/enrollment records and old event IDs and expired password reset tokens. The schema is intentionally NOT auto-applied from Vercel Functions.

## Production-only Vercel environment variables

- `DATABASE_URL` = private provider connection string (TLS required; should be supplied by provider integration)
- `EQ_TOTP_ENCRYPTION_KEY` = 32 random bytes as **64 hex characters**, generated privately and preserved across deployments. Rotation requires a data migration.
- `RESEND_API_KEY` = transactional mail provider secret; kept only in Vercel encrypted env.
- `EQ_MAIL_FROM` = verified sending address on a domain you own (e.g. `verify@yourdomain.tld`).
- `EQ_PUBLIC_ORIGIN` = `https://edgequant-mobile-web.vercel.app` (or your verified custom domain).
- `EQ_SIGNUP_ENABLED` = `1` only AFTER the provider, mail domain, migrations and tests are confirmed; omit otherwise.

Email provider setup requires user authentication and domain ownership verification. This assistant has not authenticated to or created the service. For mail delivery, use Resend's Free development allowance if eligible and within their terms, or another audited provider after adapting the sender.

## Current readiness guarantees

`GET /api/health` advertises `database_ready`, `registration_enabled`, `password_reset_ready`, `telegram_inbox_ready`, `telegram_listener_request_ready` and `worker_request_ready`. **Do not expose registration, private worker events or paid accounts while those are false.** Public registration remains OFF until the owner enables it. `live_trade_execution` is always false at this stage.

This does not deploy any database, buy hosting, connect Telegram, run an MT5 terminal, or enable live trades.
