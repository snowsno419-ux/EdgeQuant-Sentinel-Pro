# EdgeQuant Sentinel Pro — PC-style Mobile/Web + Secure Cloud Development Bridge

The same Neon Dark dashboard navigation is responsive on desktop and mobile. **Public UI is not a live trading product.**

## API modules

- Cloud health `/api/health` (feature readiness, no secrets)
- Registration `/api/signup` + `/api/resend-verification` (requires private database, verified email provider, encryption key, explicit signup feature flag)
- One-time email verification `/api/verify-email` + `/verify.html`
- Google Authenticator-compatible enrollment `/api/totp-setup`, `/api/totp-confirm`; encrypted TOTP secret
- Login `/api/login`, current user `/api/me`, logout `/api/logout`
- Forgot password `/api/forgot-password` + `/forgot-password.html`; one-use 20-minute recovery token + authenticator-protected password reset `/api/reset-password`, `/reset-password.html`. Reset revokes all sessions but preserves role and TOTP.
- DEMO broker metadata `/api/brokers`, user worker request `/api/worker-requests`
- Signed worker MT5 observations `/api/worker-observation`, read-only dashboard `/api/dashboard`
- Per-user Telegram metadata `/api/channels`, signed event intake `/api/telegram-observation`, user inbox `/api/telegram-inbox`

The registration/recovery/Telegram paths are rewritten in `vercel.json` to two Node.js gateway functions (`api/auth.js`, `api/telegram.js`), with isolated handlers in `api/_lib/routes/`. This keeps the project under the **12-function Vercel Hobby ceiling** without upgrading to a paid plan.

Everything returns read-only status. `order_send`, public Telegram OTP, private signing keys, live trade actions and customer brokerage passwords are not included. Vercel Functions cannot execute MetaTrader 5 terminals. Workers require separately provisioned Windows machines.

## Activate only when ready

Read `cloud-db/README.md` in the repository for the 8 migrations and **production-only encrypted environment variables**. Account registration is OFF until `EQ_SIGNUP_ENABLED=1` and required verified services have been connected. There is currently no managed database or Windows execution host attached to Vercel.

Local validation: `node --test tests/*.js` at repository root plus `python -m unittest discover -s tests` and syntax checks. No secrets committed to Git.

## Secure password recovery (mobile and web)

Run `cloud-db/0005_password_reset.sql` as the database owner before enabling the production reset flow. Vercel must be configured with `DATABASE_URL`, `RESEND_API_KEY`, `EQ_MAIL_FROM`, `EQ_PUBLIC_ORIGIN` and a valid Resend sender policy. `EQ_PASSWORD_RESET_ENABLED=0` can disable reset requests and completion in emergencies. Registration need not be enabled for an already verified account to reset its password.

For the free Resend test sender, only `EQ_TEST_EMAIL` receives recovery emails. Start at Login / Register → Forgot your password, request a link, open the email within 20 minutes, choose a new 12+ character password, and enter the existing 6-digit authenticator code. The reset invalidates all current login sessions; log back in. No MT5 password or Telegram secret is involved.

No password reset API response reveals whether an account exists. Request frequency is limited per email; reset guesses per token are limited. Do not copy email tokens or passwords into support chats or issue tickets.

## Login-first interface and cloud connection setup (2026-11-15)

- The public root displays the account sign-in / registration screen until `/api/me` confirms a verified, authenticated session. Only after authentication does the dashboard/navigation render. The server's per-account authentication remains authoritative; browser-only draft controls never grant access.
- After login, the first dashboard section contains **Telegram** and **MT5** setup cards. Both show actual connection status, and both begin OFFLINE. Telegram source registration is account-scoped and OFF by default.
- Telegram: register permitted channel/group numeric chat IDs, then **REQUEST CLOUD TELEGRAM LISTENER**. The request goes to the authenticated `/api/telegram-listener-requests` endpoint. It is **not** Telegram account authentication: phone OTP, 2FA, encrypted session provisioning, channel discovery and listener hosting are not built.
- MT5: register DEMO broker metadata (broker, exact server, account number) and **REQUEST DEMO CLOUD WORKER**. The existing per-account worker request records intent only. No MT5 passwords are accepted in the public web UI; a separately hosted Windows terminal with signed read-only worker observations is required for actual connection.
- Password reset remains on `/forgot-password.html`. Trading, Telegram monitoring, and broker order execution remain OFF.
- Apply `cloud-db/0006_telegram_listener_requests.sql` after the prior migrations. No paid services or worker infrastructure are activated by these screens.

## Telegram Bot + Windows DEMO MT5 pairing (2026-11-15)

A secure optional **Telegram Bot webhook** now supports administrator-verified source access with 15-minute chat proof codes, enabled/OFF read-only inbox, edited messages and update replay protection. The Bot must be added to permitted chats and configured with an operator-owned token and webhook secret on Vercel. It is not a substitute for Telegram phone OTP/MTProto private-account group discovery.

The **MT5 DEMO worker pairing** API issues a single-use 15-minute token; a separately hosted Windows terminal worker claims it by proving possession of its Ed25519 key, then the logged-in owner must approve that key fingerprint. The worker can only transmit signed account telemetry to the existing read-only dashboard. Vercel never receives broker passwords or sends orders.

Run additive migrations 0007 and 0008 in the private Neon database. Read `CLOUD_TELEGRAM_MT5_GUIDE.md` for operator setup, exact endpoints, limitations, prerequisites and client setup. Both connectors fail closed if they are not configured. No cloud Windows host or live trading enabled by source changes.

## Personal Telegram is the primary connection mode

The Telegram setup page now leads with **PERSONAL TELEGRAM ACCOUNT**, placing the Bot flow below as an optional mode. From a verified EdgeQuant account the client can request provisioning of an isolated MTProto listener **without first registering a Bot source**. Only a correctly signed worker in the authorized account scope can provide dialog names; the user can then select channel/group monitoring on/off. `cloud-db/0009_telegram_personal.sql` adds these account-scoped selections and worker heartbeat. Users can revoke the worker from the web UI.

**Important:** Browser-based phone OTP and Telegram 2FA self-service are not implemented or enabled. This source does not create or run a persistent encrypted Telegram client. Operating personal Telegram on mobile requires a hosted isolated MTProto listener, secure challenge relay, Telegram API ID/hash, encrypted per-client sessions, admin provisioning, and user consent. Read `TELEGRAM_PERSONAL_SETUP_SI.md` before offering it to clients. Bot mode stays optional; MT5 live trading remains OFF.
