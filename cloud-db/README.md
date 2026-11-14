# EdgeQuant Cloud DB — Phase 5 (staged, not provisioned)

This schema is intended for a **private managed PostgreSQL database** only. It does not create a database, provision any users or enable live trading. The deployed Vercel project intentionally returns `database_ready:false` until a real database is connected and the schema has been applied by the operator.

## Safe deployment order

1. Establish a managed PostgreSQL provider, access policy, backup/restore strategy, and a private connection on a suitable paid/authorized service when explicitly approved. Do not paste a `DATABASE_URL`, account password, MT5 terminal password, Telegram session, or worker private key into ChatGPT or GitHub.
2. Run `0001_readonly_schema.sql` manually as a restricted database schema owner. Never use the Vercel runtime user for migrations or DDL.
3. Create a separate least-privilege Vercel app role, granting only the required `SELECT/INSERT/UPDATE/DELETE` on the application tables and `USAGE` on schema `public`, not schema ownership or superuser. Limit connectivity to the Vercel deployment.
4. Configure `DATABASE_URL` as a Vercel **secret** for the production environment in the Vercel settings (not a source file). Require TLS certificate verification; keep `EQ_DB_SSL` unset in production. Use a pooling proxy if the chosen provider requires it.
5. Confirm `/api/health` reports `database_ready:true`; do not infer it from `database_configured` alone. Run auth/tenant tests in staging with generated fake users before accepting real client data.
6. Email verification and secure account provisioning are **NOT** public/signup-ready; the Phase 4 login endpoint requires an already provisioned verified user and a TOTP secret. Account provisioning, email delivery, TOTP recovery, password reset, audit logs, per-account and IP rate limiting, transaction logging, incident response, backups, and key management need review and completion before selling this service.
7. Before a DEMO worker is connected, explicitly assign broker registry ID, expected login/server, Ed25519 public key and an isolated Windows worker. Never expose the private key, never allow worker to place orders and test only against verified DEMO MT5 accounts.

## API boundaries

- `GET /api/health`: database/readiness state, not trading readiness
- `POST /api/login`: only pre-provisioned verified users with TOTP; no self-signup
- `GET /api/me`: verified session, role & account
- `GET /api/dashboard`: only that user's assigned broker observations
- `GET /api/brokers`: that user's broker metadata only (account number masked)
- `POST /api/brokers`: requires verified session, same HTTPS Origin, `mode: "DEMO"`, exact broker/server/login; **metadata only**, no MT5 login
- `POST /api/logout`: immediate revocation of the current session
- `POST /api/worker-observation`: Ed25519-signed read-only DEMO telemetry, worker/account identity enforced

**No endpoints exist for placing, modifying, closing or copying trades.** Desktop EdgeQuant execution rules remain unchanged.
