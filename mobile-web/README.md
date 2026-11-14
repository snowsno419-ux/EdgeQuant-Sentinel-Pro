# EdgeQuant Sentinel Pro — Web + Mobile / Cloud Integration Phase 4.0

**State: secure read-only bridge staged. NOT LIVE TRADING.**

The PC-style responsive Neon Dark Pro UI is connected to same-origin serverless API routes for health checks, verified-user sessions and broker telemetry. The project auto-deploys to Vercel via the GitHub `main` branch. The Windows **DEMO-only read-only worker** is developed separately, with no broker passwords or trading commands in this public web source.

## Real-data path (after provisioning)

1. Phone/PC browser displays PC-equivalent responsive UI served from Vercel over HTTPS.
2. `GET /api/health` indicates cloud API reachability and whether a DB connection is configured. This is **not** proof that MT5 is connected.
3. An administrator provisions a verified email user, TOTP secret, broker account reference and an Ed25519 public worker key in an access-controlled managed PostgreSQL database.
4. User signs in through the web profile with email + password + six-digit authenticator. The API creates an 8-hour **Secure HttpOnly SameSite=Strict** cookie session (no token stored in localStorage).
5. An **already logged-in Windows MT5 DEMO terminal** is read *only* by its assigned worker. Worker refuses mismatched broker identities and real accounts. It signs a canonical observation using the private key, POSTs to `/api/worker-observation` over HTTPS.
6. API verifies the assigned worker public key, exact broker identity, fresh timestamp, event idempotency and increasing observation time before updating the snapshot.
7. `GET /api/dashboard` returns account-isolated snapshots to the verified user only. UI refreshes every 30 seconds; stale status after 120 seconds, no fabricated balances. Browser controls remain local drafts, never send MT5 orders.

## Prerequisites and what is NOT yet done

- **Not connected** to a managed PostgreSQL database. `DATABASE_URL` must be securely configured via Vercel environment variables. A private DB migration is required before creating real users.
- **Not provisioned** for real verified email sending, TOTP recovery, secret storage, per-user broker accounts, audit, subscription/payments, production rate limits or backup.
- **No Windows DEMO worker has been enrolled or run** against an actual MT5 terminal; simulated test doubles only. Phase 3.1 read-only project remains a separate LOCAL prototype.
- **No trading execution**. No buy/sell, SL/TP, close, BE, trailing, Telegram sessions, OTP or broker credentials exposed to the website. Existing Windows EdgeQuant engine is unchanged.
- **No 100-client load test**. Production requires isolated Windows workers, monitored host capacity, Postgres auth/backup and complete security review.

## Vercel structure

- `index.html`, `styles.css`, `app.js` — desktop-like responsive UI
- `api/health.js` — unauthenticated availability, non-sensitive info only
- `api/login.js`, `api/me.js`, `api/dashboard.js` — verified account access (fail-closed while DB is missing)
- `api/worker-observation.js` — Ed25519-signed DEMO telemetry (fail-closed while DB is missing)
- `api/_lib/` — private helper modules (underscore-prefixed so Vercel does not turn them into public functions)
- `package.json` — pinned PostgreSQL driver dependency
- `../db/schema.sql` and `../cloud-worker/read_only_mt5.py` — local development reference only; not deployed with this static web site

**Security**: Vercel project must use HTTPS, a private DATABASE_URL, least-privilege DB access, verified email + TOTP, worker public keys and strict tenant isolation. Never paste live MT5 passwords or worker private keys into GitHub/Vercel source, browser inputs or ChatGPT. Do not activate server-side execution on the web host.

## Phase 5.0 — Verified DEMO broker registry (staged)

`GET /api/brokers` and `POST /api/brokers` now allow only a verified signed-in user to view/register DEMO broker metadata, without broker credentials. Account numbers are masked in responses; the registry rejects extra fields, live accounts, cross-origin requests and duplicate account/server registration. A browser-only account is not an MT5 connection; the Windows read-only worker must still be provisioned separately. `POST /api/logout` revokes a session. `/api/health` returns `database_ready` only after a real DB and expected tables are reachable; the UI remains in `DB OFF` mode otherwise.

The reviewed PostgreSQL DDL and safety steps are in `../cloud-db/`. No provider has been provisioned and no paid product activated. Self-service registration, email delivery/recovery, worker enrollment, rate limits and full production security audit are pending; do not accept live client credentials yet. Live trading remains disabled.
