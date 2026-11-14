# EdgeQuant Sentinel Pro — Email Verification Activation (සිංහල)
**Status (2026-11-14): Resend not connected. PUBLIC SIGNUP OFF. No live trading.**

## Already configured
- Neon PostgreSQL: private development project, 14 application tables
- Vercel Production `DATABASE_URL`: encrypted, limited database role `edgequant_api`
- Vercel Production `EQ_TOTP_ENCRYPTION_KEY`: encrypted random 256-bit key (never commit; DO NOT rotate without re-encrypting existing secrets)
- Vercel Production `EQ_PUBLIC_ORIGIN`: `https://edgequant-mobile-web.vercel.app`
- Vercel Production `EQ_SIGNUP_ENABLED=0` until testing passes

## Owner's required one-time service authorization
1. Go to https://vercel.com/marketplace/resend and install/connect **Resend** to the existing Vercel project `edgequant-mobile-web`. Choose a free option if offered; do not authorize a paid plan without review.
2. Resend should configure encrypted Vercel Production `RESEND_API_KEY` automatically. Never paste the key into GitHub, browser code or ChatGPT.
3. In Resend dashboard add a domain **you own**, complete requested DNS DKIM/SPF records and wait for sending verification. Vercel's `*.vercel.app` domain is NOT your sending domain.
4. In Vercel > `edgequant-mobile-web` > Settings > Environment Variables, add encrypted Production `EQ_MAIL_FROM=EdgeQuant <verify@YOUR-VERIFIED-DOMAIN>` (use your actual verified sender).
5. After provider setup, redeploy to load encrypted env vars and run end-to-end testing on a DEMO client account.

## E2E tests BEFORE enabling public signup
- Confirm Resend provider is verified and the real verification email arrives at an approved test mailbox; no real customers yet.
- The link's token goes in the fragment, expires in 20 minutes and cannot be reused.
- Verified mailbox is required before authenticator setup; 6-digit code activates TOTP.
- Login rejects unverified addresses, wrong passwords, missing/incorrect 2FA, and rate-limits bad attempts.
- Receiver/Provider role is fixed at signup; cross-user brokers and channels stay isolated.
- Check browser, HTTPS, mobile UI, session logout and no MT5 order execution.
- Only then change `EQ_SIGNUP_ENABLED=1`, redeploy, and confirm `/api/health` reports `registration_enabled:true`.

## Endpoints already in the web code
`/api/signup`, `/api/resend-verification`, `/api/verify-email`, `/api/totp-setup`, `/api/totp-confirm`, `/api/login`, `/api/logout`.

**Trading remains OFF**, and this account system is only the cloud read-only development stage. Never accept MT5 passwords or Telegram OTP on these public signup forms.
