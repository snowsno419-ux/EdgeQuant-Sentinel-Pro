# EdgeQuant Sentinel Pro — PC-style Mobile/Web + Secure Cloud Development Bridge

The same Neon Dark dashboard navigation is responsive on desktop and mobile. **Public UI is not a live trading product.**

## API modules

- Cloud health `/api/health` (feature readiness, no secrets)
- Registration `/api/signup` + `/api/resend-verification` (requires private database, verified email provider, encryption key, explicit signup feature flag)
- One-time email verification `/api/verify-email` + `/verify.html`
- Google Authenticator-compatible enrollment `/api/totp-setup`, `/api/totp-confirm`; encrypted TOTP secret
- Login `/api/login`, current user `/api/me`, logout `/api/logout`
- DEMO broker metadata `/api/brokers`, user worker request `/api/worker-requests`
- Signed worker MT5 observations `/api/worker-observation`, read-only dashboard `/api/dashboard`
- Per-user Telegram metadata `/api/channels`, signed event intake `/api/telegram-observation`, user inbox `/api/telegram-inbox`

Everything returns read-only status. `order_send`, public Telegram OTP, private signing keys, live trade actions and customer brokerage passwords are not included. Vercel Functions cannot execute MetaTrader 5 terminals. Workers require separately provisioned Windows machines.

## Activate only when ready

Read `cloud-db/README.md` in the repository for the 4 migrations and **production-only encrypted environment variables**. Account registration is OFF until `EQ_SIGNUP_ENABLED=1` and required verified services have been connected. There is currently no managed database or Windows execution host attached to Vercel.

Local validation: `node --test tests/*.js` at repository root plus `python -m unittest discover -s tests` and syntax checks. No secrets committed to Git.
