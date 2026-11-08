# EdgeQuant Sentinel Pro — PHONE ONLY / NO-PC CLIENT Architecture

## Owner Requirement (MANDATORY)

Android/iPhone phone එකක් පමණක් තිබෙන client කෙනෙක්ට EdgeQuant web/PWA එකෙන් සම්පූර්ණ onboarding, MT5 broker link, Telegram source setup, DEMO test, authorized live activation, dashboard, remote trade controls ලබාදෙන්න. Client PC, Windows installer, user-managed VPS, RDP, Python, local terminal install **අනිවාර්ය නෑ**. EdgeQuant platform එක per-tenant/worker isolated managed Windows MT5 infrastructure ලබාදිය යුතුය.

### Two Modes
- **Managed Cloud (DEFAULT):** Owner hosts/operates isolated Windows worker + MT5 terminal (prefer dedicated VM per tenant baseline); cloud/API coordinates, phone UI monitors. Tenant resources provisioned automatically and costs factored into license.
- **BYO Windows Agent (OPTIONAL):** Advanced client may use own Windows PC/VPS; browser shows offline when it is OFF. This is not the default requirement.

### Flow
Mobile Web/PWA → Auth + license → Managed Host Provisioner → Isolated Windows MT5/Telegram worker → Broker MT5 Account. User's phone may go offline without killing worker, provided server, broker, Telegram and network remain healthy.

### Core Components
Next.js TypeScript Mobile-first UI, Node.js/TypeScript API, PostgreSQL, auth/RBAC+tenant security, managed Windows VM worker provisioner and lifecycle, KMS encrypted per-tenant broker credentials, native MT5 Python integration, Telegram listener per approved provider, durable SQLite WAL/inbox/outbox, ticket reconciliation, duplicate guard, risk policy, status/alerts and billing.

### Critical Controls
- User cannot see other clients' data or host; no tenant-shared MT5 terminal secrets.
- Do not store broker secrets or Telegram code/session plaintext in browser/localStorage/logs.
- Client chooses demo first and explicitly enables live. Broker acceptance is not guaranteed; never fabricate confirmations.
- On VM/MT5/Telegram failure show actionable offline/degraded statuses, retry safely only after reconciliation.
- Host migration is transactional and protects 2-layer orders against duplicates.
- An expired license must not strand open positions without safe management/cancellation path.
- **Do not treat MetaTrader built-in Virtual Hosting as a general Python/Telethon Windows VPS.** It does not provide arbitrary desktop program execution.

### Minimum Tests
1. User with smartphone ONLY: no PC, no installer; connect MT5 demo/Telegram from mobile with platform managed hosting.
2. Client phone OFF, managed Windows worker on: Telegram signal still processed when services healthy.
3. Two separate tenants: no access/leakage/orders/credentials across tenants.
4. Multiple brokers: separate account/terminal tickets and statuses; no cross-account fallback.
5. Worker offline/restart: status, reconciliation, no blind retry/duplicates.
6. Existing owner trading rules 2-layer, XAUUSD offsets, shared SL, adjustable TP1, TP2, 50/150 fallbacks, edits, expiry, BE, risk, duplicate guard unchanged.
7. Real managed Windows VM provisioning + terminal session auto-start tested on Windows demo, not only mock.

### Deployment proof
Show real IaC/provisioner source, Windows bootstrap, platform deployment guide, secure onboarding, live demo verification report, and infrastructure cost plan. If cloud credentials unavailable, fake provisioner/unit tests are permitted for development **only** and must be marked NOT_VERIFIED as a deployable cloud product.

This file is a mandatory owner amendment to `01_MASTER_PROMPT_SI.md`, though the master has also been updated to include these rules.
