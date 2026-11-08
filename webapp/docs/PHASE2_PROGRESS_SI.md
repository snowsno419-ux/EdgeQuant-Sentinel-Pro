# EdgeQuant Sentinel Pro — Phase 2 Development Checkpoint

මෙම branch එකේ Phase-2 security/database development පටන් ගෙන ඇත. සම්පූර්ණ source snapshot එක ChatGPT conversation එකේ `EdgeQuant_Sentinel_Pro_WebApp_Phase2_20261108.zip` නමින් ලබාදී ඇත.

## Local working snapshot
- Fastify REST endpoints: register, verify email, resend verification, login, logout, me, broker metadata list/register
- PostgreSQL tenant/user/session/email verification/account/audit schema
- Scrypt password hashing, hashed session tokens, strict SameSite HttpOnly cookies
- Receiver/Provider public signup only; one-time Owner bootstrap helper
- Next.js login / email verification / secure broker-portal screens
- Existing Telegram 2-layer vs Direct MT5 copy planning kept separate
- **23/23 Node unit & static tests passed** in local ZIP
- **npm package installation timed out** in the current environment; API/Next production build and actual PostgreSQL integration not verified

## Safety / launch status
Live MT5 connection, provider-to-follower trade copying, email SMTP delivery, license/payments, Windows cloud workers are **NOT IMPLEMENTED / NOT VERIFIED** in this checkpoint. All preview balances are sample data. No live trading is enabled.

**This GitHub branch is currently a partial checkpoint, not a synchronized copy of every file in the conversation ZIP.** Until all remaining files are pushed, use the attached ZIP for the complete Phase-2 source snapshot.

Never push .env, customer account credentials, Telegram session files or MT5 passwords.