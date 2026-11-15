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

Read `cloud-db/README.md` in the repository for the 4 migrations and **production-only encrypted environment variables**. Account registration is OFF until `EQ_SIGNUP_ENABLED=1` and required verified services have been connected. There is currently no managed database or Windows execution host attached to Vercel.

Local validation: `node --test tests/*.js` at repository root plus `python -m unittest discover -s tests` and syntax checks. No secrets committed to Git.

## Secure password recovery (mobile and web)

Run `cloud-db/0005_password_reset.sql` as the database owner before enabling the production reset flow. Vercel must be configured with `DATABASE_URL`, `RESEND_API_KEY`, `EQ_MAIL_FROM`, `EQ_PUBLIC_ORIGIN` and a valid Resend sender policy. `EQ_PASSWORD_RESET_ENABLED=0` can disable reset requests and completion in emergencies. Registration need not be enabled for an already verified account to reset its password.

For the free Resend test sender, only `EQ_TEST_EMAIL` receives recovery emails. Start at Login / Register → Forgot your password, request a link, open the email within 20 minutes, choose a new 12+ character password, and enter the existing 6-digit authenticator code. The reset invalidates all current login sessions; log back in. No MT5 password or Telegram secret is involved.

No password reset API response reveals whether an account exists. Request frequency is limited per email; reset guesses per token are limited. Do not copy email tokens or passwords into support chats or issue tickets.
