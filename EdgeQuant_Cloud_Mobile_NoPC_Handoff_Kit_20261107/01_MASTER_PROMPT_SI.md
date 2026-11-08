# EDGEQUANT SENTINEL PRO — FULL WEB APP MIGRATION & IMPLEMENTATION MASTER PROMPT

> මේ prompt එක Claude Code / Claude coding agent / GPT-6.1 Sol හෝ ඊට සමාන repository-editing coding agent එකකට දෙන්න. මේ prompt සමඟ **EdgeQuant_Duplicate_Entry_Protection_20261107.zip**, **EdgeQuant_Sentinel_V2_Architecture_Implementation_Plan.md**, තිබෙන brand assets, අවශ්‍ය screenshots upload කරන්න. Source ZIP එක attach කරලා නැත්නම් එය ලබාගන්න කියන්න; කිසිම අවස්ථාවක source code තිබෙනවා වගේ අනුමාන කරන්න එපා.

## 0. ඔබගේ කාර්යභාරය සහ අවසන් අරමුණ

ඔබ Senior Full-Stack Architect, FinTech/Trading Systems Engineer, MT5 Integration Expert, Telegram Integration Engineer, Windows Service Engineer, QA/Security Engineer සහ Product Designer ලෙස වැඩ කරන්න.

**මට conceptual design එකක් විතරක් එපා. දැනට තියෙන සම්පූර්ණ EdgeQuant Sentinel Windows desktop project එක සලකා බලා, source එක ඇත්තටම inspect කර, existing functionality preserve කර, production-oriented, installable, runnable, sellable, responsive Web SaaS platform එකක් සඳහා real working code, tests, migrations, documentation, deployment files, setup instructions සහ ZIP deliverable එකක් නිර්මාණය කරන්න.**

**OWNER'S HIGHEST-PRIORITY PRODUCT REQUIREMENT: PC එකක් නැති client කෙනෙකුට Android/iPhone එකක් පමණක් තිබුණත් EdgeQuant එකට sign up වී MT5 account link කර, Telegram signals follow කර, trades monitor/manage කර, automation 24/7 භාවිත කළ හැකිවිය යුතුයි. Clientට Windows PC, VPS/RDP, Python, installer හෝ MT5 desktop terminal install/operate කිරීම අනිවාර්ය නොකරන්න. අපේ PLATFORM එක managed Windows MT5 infrastructure ලබාදිය යුතුයි. Existing self-hosted Windows-agent option එක optional alternative එකක් ලෙස පමණක් පවත්වාගන්න.**

Product name: **EdgeQuant Sentinel Pro**. Existing **EdgeQuant EQ** official branding, icon, logo, colors සහ watermark assets තියෙනවා නම් ඒවා reuse කරන්න. Generic logo දාන්න එපා.

Userට implementation progress සිංහලෙන් පැහැදිලි කරන්න. Code, filenames, database schema, APIs සහ command examples English වලින් ලියන්න. එක් එක් phase එක අවසන් වුණාම ඇත්තටම run/test කළ results කියන්න. **Mock demo එක production MT5 implementation එකක් ලෙස නොපෙන්වන්න.**

## 1. Input project: source audit අනිවාර්යයි

Source ZIP එක extract කර පහත files හා ඇත්ත functionality පරීක්ෂා කරන්න:

- `edgequant_auto.py` — Telegram→MT5 signal/trade execution foundation.
- `edgequant_desktop.py` — desktop UI/settings වල existing business behavior.
- `edgequant_parallel_mt5.py` — isolated broker worker fan-out.
- `edgequant_duplicate_guard.py` — account-scoped duplicate entry guard, persisted claims.
- `edgequant_signal_updates.py`, `edgequant_vip_signal_edits.py`, `edgequant_vip_updates.py`, `edgequant_vip_format.py` — edits/replies, VIP parser, signal management.
- `edgequant_web_agent.py`, `edgequant_cloud.py`, `edgequant_remote_agent.py` — පැරණි local/web/cloud integrations (trust boundaries review කරන්න).
- `edgequant_broker_dashboard.py`, `provider_studio.py`, `signal_parser.py`, `edgequant_limit_daily.py`, `edgequant_sinhala_voice_worker.py`.
- `requirements.txt`, `supabase/schema.sql`, `EdgeQuantSentinel-Client.iss`, brand icon/logo assets, tests, README and changelogs.

ඉස්සෙල්ලා **SOURCE AUDIT REPORT** ලියන්න: feature inventory, retained/rewritten/deprecated modules, source conflicts, security gaps, data locations, current tests, migration strategy. Source file එකක් නොතිබුණොත් report එකේ missing කියන්න. Historical README instructions newer owner requirements වලට conflict නම් owner requirements වලට priority දෙන්න; behavior tests මගින් verify කරන්න.

**AI Agent/self-directed trading feature එක නැවත හදන්න එපා.** Deterministic rules හා owner-configurable automated modules පමණක්. Preserve existing trading features, Provider Studio, broker dashboards, journal/reporting, Telegram provider settings, login/session handling, alerts, user configuration සහ branding wherever technically applicable. Unsupported legacy desktop-only feature එකක් තිබුණොත් exact migration map එකක් දෙන්න—silent removal එපා.

## 2. Target architecture (ඉතා වැදගත්)

Web UI එක Windows desktop app එකක් embed කිරීමක් නොවිය යුතුයි. Browser/mobile එකෙන් use කරන්න පුළුවන් real web app එකක් හදන්න.

- **Frontend:** Next.js App Router + React + TypeScript + Tailwind CSS + shadcn/ui (හෝ same-grade accessible UI kit), TanStack Query, typed API client, mobile-first PWA.
- **Cloud API:** Node.js + TypeScript, NestJS හෝ Fastify (project එකට සුදුසු එකක් තෝරා rationale දෙන්න); REST + authenticated WebSocket/SSE for real-time events.
- **Cloud DB:** PostgreSQL + Prisma/Drizzle migrations; Redis/BullMQ only when queue/durable delivery justifies it. Multi-tenant isolation.
- **Trading Worker:** Existing Python MT5/Telethon execution code එක managed **cloud Windows VM/VPS execution worker (DEFAULT)** එකකට සහ optional client-owned Windows worker (BYO) එකකට refactor කරන්න. MT5 terminal එක Windows host එකක run විය යුතුයි; එය phone එකේ install කරන්න එපා. Python end-user-facing Web UI එක සඳහා භාවිත කරන්න එපා; native Windows MT5 bridge සඳහා පමණක් පිළිගන්න. Broker account එකකට separate MT5 terminal/process/account isolation. Managed hosts සම්බන්ධයෙන් tenant isolation, lifecycle, patching, uptime, health monitoring සහ remote diagnostics platform එකේ වගකීමක්.
- **Windows bridge:** Encrypted outbound HTTPS/WebSocket connection to server; signed, scoped, replay-protected commands; durable offline local queue; heartbeats; service auto-start. Managed mode: cloud provisioner auto-allocates host/worker; phone onboarding never requires QR pairing to a client PC. BYO mode only: optional QR/one-time agent pairing. Managed secrets must be encrypted using centralized KMS/envelope encryption plus host/service identity and tightly scoped runtime access; BYO agent can use Windows DPAPI. Never assume DPAPI alone is a portable cloud secrets solution.
- **Local state:** SQLite (WAL) + transactional outbox + existing claim files migration. Offline execution/reconciliation when appropriate; cloud/browser downtime should not stop a locally authorized MT5 worker.
- **Cloud security:** HttpOnly secure sessions, MFA support, RBAC, per-tenant auth, audit logs, secrets management, TLS, rate limits, encryption at rest, CSRF protection where applicable.
- **Deployment:** Web/API/PostgreSQL on suitable cloud Linux infrastructure (Docker Compose development; production deployment guide), **platform-managed isolated Windows VM/VPS pool for MT5 + Telegram execution**. Optional BYO Windows PC/VPS mode for advanced clients. Clientට device එකක් ලෙස phone එක පමණක් තිබීම fully supported; phone browser/PWA එකට MT5 terminal හෝ Windows service install කළ යුතු නැහැ. Billing plans must account for real always-on Windows compute cost.

Project root monorepo structure (adapt if needed):

```text
edgequant-sentinel-pro/
  apps/web/                  # Next.js PWA
  apps/api/                  # TypeScript cloud API
  apps/admin/                # Can be routes inside web if simpler
  packages/contracts/        # shared schemas/types/events
  packages/ui/               # reusable branded components
  bridge/windows-agent/      # existing Python code refactored to Windows service
  bridge/mt5/                # broker worker, MT5 adapter and reconciler
  bridge/telegram/           # Telethon connector, parsing, revisions
  infra/docker/              # compose, db, Redis optional
  infra/windows/             # service install/update/uninstall, logging
  docs/                      # Sinhala setup, security, operation, migration
  tests/                     # unit, integration, e2e, simulated MT5
  scripts/
  .env.example
  README-SI.md
```

**Browser/cloud API alone cannot directly place MetaTrader5 Python-native orders.** Don't claim otherwise. Default product flow uses platform-provisioned always-on Windows trading host; therefore **client phone OFF, phone browser closed or client has NO PC must not stop trading** while managed host and upstream services remain healthy. Optional BYO mode: local PC OFF means its agent offline. If managed host, broker or Telegram becomes unavailable, show honest offline/degraded state and attempt safe recovery, never guarantee 100% uptime or forced broker acceptance. **Do not substitute MQL5 integrated Virtual Hosting for a general Python/Telethon Windows host** without proving external programs supported; default is managed Windows VM/VPS.

## 2A. NO-PC CLIENT FIRST — MANAGED CLOUD MT5 EXECUTION (OWNER MANDATORY)

මෙම section එක optional enhancement එකක් නොවෙයි. Existing source/project requirements වල "client PC එකේ agent install කරන්න" යන wording එකට conflict වුණොත් **මෙම mobile-only managed deployment requirement එකට priority දෙන්න.** Full 10-feature implementation සහ historical owner trading rules ඒ විදිහටම preserve කරන්න.

### 2A.1 Deployment modes

1. **MANAGED_CLOUD (default, required, commercial):** Clientට phone/browser එකක් සහ internet access එකක් පමණක් අවශ්‍යයි. EdgeQuant platform backend එක client tenant එකට managed Windows MT5 host/worker provision කරනවා. Clientව තමන්ගේ Windows PC/VPS/RDP මිලදී ගන්න, setup කරන්න, login වෙන්න හෝ MT5 terminal download කරන්න කියලා අනිවාර්ය කරන්න එපා. Host provisioning automatic සම්පූර්ණයෙන් configure කළ infrastructure credentials සමඟ කළ යුතුයි; credentials නැති local dev environment එකේ real cloud provision නොකර test adapter යොදා truthful state පෙන්වන්න.
2. **SELF_HOSTED_AGENT (optional):** Existing PC/VPS-based agent installation for technical clients. Both modes share ONE domain trading-engine contract, duplicate protection, security, user settings, APIs, order state machine, analytics and license enforcement. Don't create separate rule sets. Migrating between modes must reconcile tickets before enabling trading.
3. Provisioning is **a platform obligation**; "buy your own Windows VPS" is NOT a valid response to a no-PC user. Client may choose managed plan and pay for managed resources through subscription.

### 2A.2 Mobile-first onboarding; phone-only E2E

Required sequence from smartphone without computer:

1. Open branded EdgeQuant URL/PWA → create/login account, verify identity as needed, enable MFA, choose Managed Cloud plan and activate trial/license/subscription.
2. Tap **Connect MT5** → enter broker/server/login and trading authorization through secure authenticated form. Explain investor/read-only passwords cannot execute trades; never collect or echo codes/passwords in support chat. Provide explicit consent and revocation. Broker-specific verification (incl any OTP/MFA) must use secure workflow if supported; never claim all brokers can be automated without manual verification.
3. Platform securely stores connection secrets with KMS/envelope encryption and tenant-scoped access. Provision isolated managed Windows worker. Install/launch correct MT5 terminal, map exact account login+server, verify read/write permissions, report `PROVISIONING → CONNECTING → CONNECTED / ACTION_REQUIRED / ERROR`. Client must never receive Windows desktop installer instructions.
4. From phone choose Telegram signal sources and grant only legitimate authorized access: provider bot/channel integration where supported or managed tenant-specific authenticated Telegram integration with explicit session consent, encrypted session/token storage and secure login-code flow. Avoid shared Telegram session across tenants, unauthorized channel access, leaking Telegram codes to logs, or promising unsupported sources.
5. Configure owner trading rules (two layers, limits, SL/TP, duplicate guard, risk, expiry, edits, multi-broker), run a **DEMO account test** with explicit confirmation; separately confirm enabling LIVE orders. Show broker and worker health.
6. Phone/browser can close, lose internet, or power off; managed Windows host and Telegram listener continue operating independently when hosting + broker + Telegram services are healthy. When client reconnects, read real broker results, never simulate pending order accepted/filled state.
7. From phone securely pause/resume automation, modify allowed settings, cancel pending, close authorized positions with confirmations and server-side permissions; full audit history and notifications.

### 2A.3 Managed infrastructure design

- Cloud provisioning service + worker registry + job scheduler + agent heartbeats + broker account identity registry. At baseline **dedicated Windows VM per tenant** for strong isolation (or demonstrate and test equivalent isolation if proposing shared resource pools); separate MT5 terminal/profile/process per broker account, no shared credentials/terminal data directories between clients. Avoid assuming Windows GUI MT5 runs correctly in generic Linux containers or a noninteractive service-only session.
- Deployment must document reliable Windows GUI terminal session strategy (autostart without active RDP, reboot recovery, Windows updates, crash monitoring, service/Task Scheduler or equivalent), MT5 EULA/provider policies and supported broker restrictions. Actually validate behavior on Windows hosts; cloud deployment unverified until tested.
- Cloud control plane issues signed scoped commands; Windows execution plane handles native MT5 and tenant-scoped Telegram ingestion. Durable inbox/outbox, SQLite WAL, transactionally tracked idempotency, reconciliation after restart, per-account order tickets, rate limits and account/tenant safeguards.
- Provision, pause, unprovision, back up, reconnect and migrate hosts safely. Host migration must pause new submissions, reconcile exact broker tickets, restore claims/revisions and only then resume to prevent duplicate orders. If managed worker is unavailable, show `CLOUD_AGENT_OFFLINE` and notify user; do not silently skip or fake executed signals.
- Live metrics: worker online status, broker connected status, Telegram connected status, last heartbeat, queue backlog, last broker rejection, host region, resource plan, subscription status. No fake realtime chart numbers.
- Design capacity/cost controls: monthly Windows VM licensing/compute, storage, network, broker count, provider sessions, high availability, quotas, plan pricing, client suspension/grace. Never claim unlimited Windows instances at fixed zero cost.

### 2A.4 Dedicated security boundary

- Cloud-managed broker secrets need a **managed secrets vault / KMS**; strict tenant-scoped envelope encryption, TLS, worker identity, least-privilege read during connection, access logs, rotation and revocation. Never store broker passwords plaintext in browser localStorage, database tables, log files, build artifacts or URLs. For BYO agent Windows DPAPI may be used, but not assumed as universal cloud secret store.
- Separate tenant identities, roles, API tokens, runtime file systems, Telegram session files, account login/server and trade queues. Signed commands must bind `tenant_id`, `account_id`, action, nonce, expiry, authorization and audit record. Test cross-tenant leakage and compromised worker key revocation.
- Zero shared Windows admin password between tenants, restricted RDP/admin, platform-operator support access audited and time-scoped. Apply KMS key policies, backup encryption, data retention/delete, incident response and legal/privacy obligations.
- On user disconnect/account removal/expired plan, revoke access and stop **new** order creation as policy requires, but allow safe management/cancellation/reconciliation for existing positions. Handle cloud resource shutdown carefully; no stranded unmanaged positions.

### 2A.5 New user-facing pages and APIs

- **Mobile Cloud Setup Wizard**: Account → Managed Cloud subscription → Connect Broker → Connect Telegram → Demo Test → Enable Live.
- **Cloud Host / Connections**: status `NOT_PROVISIONED`, `PROVISIONING`, `READY`, `BROKER_CONNECTED`, `ACTION_REQUIRED`, `DEGRADED`, `OFFLINE`, `SUSPENDED`, with retry and detailed reason.
- **Owner Admin**: provisioned tenants, per-tenant Windows VMs/workers, provisioning failures, broker/Telegram health, subscriptions and hosting cost visibility, secure worker restart/migration, audit logs.
- Database: add `hosting_plans`, `managed_hosts`, `host_provisioning_jobs`, `worker_instances`, `worker_heartbeats`, `tenant_host_assignments`, `broker_connection_grants`, `secret_references`, `host_migrations`, `hosting_usage`, `subscription_entitlements`; external secret payloads must not be stored as raw DB fields.
- API: `POST /api/v1/hosting/managed/provision`, `GET /api/v1/hosting/status`, `POST /api/v1/hosting/managed/reconnect`, `POST /api/v1/brokers/connect`, `POST /api/v1/hosting/migrate`, `GET /api/v1/hosting/usage`; user-only endpoints enforce tenant/account ownership; operator endpoints require audited admin privilege. Define idempotency, body schemas and error formats.

### 2A.6 Mandatory no-PC acceptance tests

- NC1: Fresh tenant completes onboarding from Android or iPhone browser without any Windows computer or local bridge installation.
- NC2: Managed worker attaches the exact authorized MT5 demo account and Telegram source; sends owner two-layer signal through actual connector; broker confirmation/rejection is shown accurately.
- NC3: Client phone switched OFF; a permitted signal still reaches always-on managed worker and is processed, provided upstream network/services stay available. Phone reconnect shows true state.
- NC4: Tenant A cannot view, alter, connect or trade Tenant B account and cannot access its host/session/secrets, even by forged API requests.
- NC5: One Windows VM/worker crashes or is rebooted → platform status/alert, restart, broker reconciliation, no duplicate 2-layer pair.
- NC6: Broker credential invalid/read-only, expired hosting plan, missing MT5 terminal, no Windows session, cloud provider provisioning quota failure → explicit actionable status, no fabricated trade success.
- NC7: License expiration/host migration still permits documented existing-position safety actions; no unauthorized fresh entry.
- NC8: Add second broker from phone → isolated terminal+account execution and broker-wise P&L; no fallback to another account.
- NC9: Agent/browser/Telegram disconnects and reconnects → durable processed message revisions; no duplicate edit or signal placement.

**Proof requirement:** Provide real managed-host infrastructure adapters + deployment IaC (e.g. Terraform/PowerShell bootstrap), executable worker setup, CLI/admin provisioning instructions, tests and cost/operations notes. If cloud credentials or Windows VM are unavailable, complete code + fake adapter tests **but label actual phone-only live execution `NOT_YET_VERIFIED`**. Mock cloud host is not a completed managed hosting service.

## 3. Non-negotiable EXISTING OWNER TRADING RULES — වෙනස් කරන්න එපා

**3.1 Signal order rules**
- Telegram group එකක parseable BUY LIMIT / SELL LIMIT signal එකක් ආවම, එක් original signal entry level එකකට **layers 2** (two independent intended orders), එක් enabled/authorized MT5 account එකකට.
- Explicit signal entry එක MT5ට submit කිරීමට පෙර **current Bid/Ask comparison එකක් කරලා app-level reject/skip නොකරන්න**. Market price chase කරන්න එපා; LIMIT වෙනුවට STOP හෝ MARKET නිහඬව switch කරන්න එපා.
- **Gold/XAUUSD fixed owner adjustment:** BUY adjusted entry = original entry `+0.99` price units; SELL adjusted entry = original entry `-0.90` price units. මේක dynamic spread calculation එකක් නොවෙයි. Userගේ owner configuration මගින් versioned configurable කළ හැකිවුණත් default එක පවත්වාගන්න. Other symbols: specified original entry (unless expressly configured otherwise).
- **Layer 1 TP:** adjusted entry සිට **50 instrument-defined pips** by default; Dashboard එකෙන් userට වෙනස් කළ හැකි. Layer 2 TP: signal TP exact; නැත්නම් adjusted entry සිට default **150 instrument pips**.
- **BOTH layers SL එකමයි:** signal SL දීලා තියෙනවා නම් දෙකටම ඒ exact SL. Signal SL missing නම් adjusted entry සිට proper direction එකට **50 defined pips** fallback SL.
- BUY/SELL side අනුව pip direction correct; broker tick size/digits/contract spec/volume step validation. Gold pips `0.01`, `0.1`, `1` වගේ අනුමාන නොකර configurable `pip_size` per normalized symbol සහ broker metadata අවශ්‍යයි.
- Signal TP/SL නැතිවීම නිසා default Manual Review gate එකක් නැහැ. Defaults දාලා plan එක build කරන්න. Unparseable/ambiguous signal එකක් **අනුමාන කර live trade කරන්න එපා**.
- MT5 broker invalid LIMIT price, stops, freeze levels, margin, market closed වැනි server-side rules නිසා reject කළ හැකියි. **Broker restriction bypass කරන්න බැහැ.** `BROKER_REJECTED` + retcode + comment + proposed order details ලෙස UI එකේ පැහැදිලිව පෙන්වන්න. Submission ≠ accepted order ≠ filled trade.
- Account OFF, emergency stop, configured risk caps, lack of authorization/license, inability to identify exact account, failure to persist idempotency claim: properly **BLOCKED** ලෙස පෙන්වන්න. Owner's “do not silently miss signals” goal එක achieve කරන්න via durable inbox, statuses, retry/reconciliation for safe failures; unsafe blind retries/forced acceptance එපා.

**3.2 Duplicate protection (must be exactly correct)**
- New signal duplicate identity per **MT5 account login+server**, normalized symbol incl suffix, BUY/SELL side, **original** entry, resolved SL, signal or resolved Layer-2 TP.
- Same Entry + SL + TP signal එක Telegram වෙනත් chat එකකින්, message ID එකකින් හෝ restart පසු නැවත ආවත් **no new pair**. Layer 1 configurable TP identity එකට නොගන්න.
- Entry range එකක 2 levels නම් duplicate level පමණක් skip කර, අලුත් original entry level එකට pair එක create කරන්න.
- Duplicate detection order concurrency-safe, crash-safe, per-account scoped, with DB unique keys and durable claims; old `%LOCALAPPDATA%\EdgeQuant\duplicate_signal_claims_v1\` import/reconcile කරන්න.
- Existing MT5 orders, pending tickets, positions/history and local state reconcile කරන්න. Uncertain send result = **UNKNOWN_RECONCILE**, NEVER blind resend. Definitive rejection audit; safe retry policy explicit and reconciled.

**3.3 Telegram edit/reply rules**
- Original Telegram message edit හෝ original signal එකට reply/mention කර Sinhala, Singlish, English වලින් “entry eka 4050ta ganna SL eka 4000ta tiyanna” කිව්වොත් original message reference අනුව **එම MT5 account එකේ තනි signal/order pair** match කරන්න.
- Example original `GOLD BUY 4000 SL 3950 TP 4100`; later reply `entry eka 4050ta ganna SL eka 4000ta tiyanna` → pending layers දෙකේ adjusted entry `4050.99`, shared SL `4000`, Layer 1 configured quick TP new adjusted entry අනුව recalculate, Layer 2 TP still `4100`.
- Pending orders modify; already filled position එකේ entry price change කළ නොහැක. Open position SL/TP පමණක් broker policy සහ explicit command අනුව modify. Ambiguous replies wrong ticket එකකට apply කරන්න එපා. Audit revision and MT5 accepted/rejected status.
- NewSignal, MessageEdited, Reply, reconnect replay and variations of VIP/limit formats support. Sinhala Unicode + Singlish variants + English parser regression test corpus.

**3.4 Other owner settings**
- AI Agent removed; don't add self-directed model-based trade decision feature.
- Max total open orders, max live per symbol, max pending per symbol all user configurable. `0` = no app-level cap; doesn't bypass broker margin/risk/safety.
- Existing separate Auto BE, trailing stop and other safe features preserve and test. Keep broker MAIN plus independent optional additional brokers and broker-wise P&L. USC cent-account normalization display as needed without modifying actual broker data.
- Preserve historical brand EQ logo in web favicon, PWA icons, login, loading splash, and marketing/admin UI.

## 4. ALL TEN NEW FEATURES — IMPLEMENT REAL MODULES

### F01 — Smart Risk Manager
Per-account risk: fixed lot/risk-based lot modes, max per-trade risk %, daily monetary loss limit, max drawdown, equity protection, available margin checks, spread/commission estimation, correlated symbol exposure, per-symbol and total live/pending limits. Use broker tick/pip/contract metadata and `order_calc_profit` where suitable. Risk blocks do not silently alter signal price, SL, TP. UI shows reason, owner settings, snapshot. Emergency kill switch must continue allowing safe cancel/close/reconciliation.

### F02 — MT5 Order Recovery & Reconciliation
Persist every signal and every layer order intent **before** sending. Durable state machine: `RECEIVED`, `PARSED`, `DUPLICATE`, `RISK_BLOCKED`, `QUEUED`, `SENDING`, `CONFIRMED_PENDING`, `FILLED`, `PARTIALLY_FILLED`, `BROKER_REJECTED`, `UNKNOWN_RECONCILE`, `EXPIRED`, `CANCELLED`, `CLOSED`. Use per-broker `orders_get`, `positions_get`, history orders/deals, magic/comment/tickets; handle reconnect, timeout, crash, delayed broker result without duplicate trades. Expose attempt audit, replay-safe commands and live diagnostics.

### F03 — Advanced Telegram Commands
Multilingual English/Singlish/Sinhala commands: new signal, edit entry, edit SL, edit TP, cancel pending, hold/resume trading per provider, move to BE, close half, close full, partial close percentage, 'do not buy again', explicit TP1/TP2/SL hit updates. Match original chat/message or uniquely correlated signal; never guess wrong trade. Typed command parser, permissions, validation, immutable event log; delete/edit precedence and tests.

### F04 — Multi-Broker Execution
MAIN plus unlimited configurable extra connected MT5 accounts (practical resources apply). One isolated Windows terminal/worker per broker and account login/server checks, custom symbol suffix mappings, broker-specific spreads, precision, risk, balance/equity/P&L. Fan-out independent per broker. Failed account cannot fall back to MAIN and must not modify another account. Support hedging versus netting limitations; clear warning on netting accounts where independent logical layers cannot map to separate open positions.

### F05 — Advanced Trade Analytics
Dashboard: live account balance/equity, broker-wise real P&L, realized/unrealized, win rate, profit factor, expectancy, RR, max drawdown, day/week/month/year, calendar, symbol/provider/channel/strategy performance, rejection rate, execution latency, duplicate signal stats. Read actual broker deals incl commission/swap/fees; don't count pending orders as closed profits, avoid partial-close double counting. Excel/PDF export from actual structured data with branding. USD/USC display conversion handled correctly.

### F06 — Signal Expiry
Configurable pending order expiry by minutes, provider, symbol and explicit signal expiry; app-level order lifecycle and broker pending-order removal. Filled trades must never be cancelled by pending expiry routine. Network outage recovery and race-safe cancellation; show `EXPIRED`, `CANCEL_FAILED` reasons. Optional default expiry OFF unless explicitly set.

### F07 — Smart BE, TP1/TP2 & Partial Take Profit
Layer 1 has independent configured 50-pip quick TP. If Layer 1 TP confirmed filled/closed, optional user-enabled Layer 2 SL→BE or BE+buffer policy; never move protective SL backwards. Support partial closes with volume step/min lot checks, fixed percent and manual commands. Proper hedging/netting handling, no unrelated position modifications. Ensure broker confirms every modification.

### F08 — Real Mobile Responsive Web Dashboard
Not a static preview: live PWA for desktop/tablet/mobile with login, dashboard, signals, trades, brokers, account status, analytics, news/notifications, settings, journal, Provider Studio as suitable, licenses, backup status. Browser may be closed without stopping Windows worker. Start read-only monitoring then enable explicitly authorized remote pause/resume, cancel pending, close position via signed queue and confirmation; all logged. Dark premium fintech UI, left collapsible sidebar on desktop, bottom nav/mobile drawer on small screens. Loading/empty/error/offline/reconnected states all implement.

### F09 — Client License & Subscription System
Owner/admin panel, client tenant register/login, trial, subscription plans Basic/Pro/Business, license keys, device activation, seats, active/expired/grace, broker limits by plan, server-signed entitlements, device revoke, subscription renewal, payment provider integration boundary (use real provider test mode if configured, otherwise explicitly mark setup as pending; do not fake successful payments). On license expiry: block **new orders** but allow existing position safety management, cancellation, reconciliation and withdrawal of credentials. Tenant isolation, support roles, audit logs.

### F10 — Auto Backup & Disaster Recovery
Versioned local snapshots of settings, state DB, broker mapping, Telegram signal revisions, journal, duplicate claims, audit trail; encrypted optional cloud storage with scheduled retention and recovery checks. Secrets: don't upload raw broker passwords, Telegram `.session` files or DPAPI data to cloud by default. Restore preview, checksum, schema migrations, backup browser and tested restore. **Before trading resumes after restore, reconcile against live MT5** to prevent duplicates.

## 5. UI/UX — Required Pages

Build professional consistent EdgeQuant EQ brand theme. Navigation:
`Overview / Live Dashboard`, `Telegram Signals`, `Pending Orders`, `Open Positions`, `Trade History`, `Brokers & MT5`, `Risk Manager`, `Signal Rules & Providers`, `Commands & Edits`, `Analytics & Reports`, `Trade Journal`, `Signal Expiry`, `Backups & Recovery`, `Notifications`, `License & Billing`, `Settings`, and `Owner Admin` (role protected).

Each page needs real APIs, functional buttons, validation, skeleton loading, empty and error states, real-time events, responsive tables/cards. No inert demo buttons. Chart components for actual live data, searchable/sortable/filterable trade tables, MT5 retcode display, P&L charts, forex/USD/USC units. Passwords/keys never displayed in plaintext or browser logs. Role-specific sidebar options. Add mandatory **phone-only managed onboarding**: 1) register/login from mobile 2) activate managed-cloud license/plan 3) automatic managed Windows worker provisioning (NO CLIENT INSTALLER) 4) connect MT5 broker via secure mobile form 5) connect authorized Telegram source 6) demo-test order 7) enable live with explicit confirmation. Optional advanced users may select BYO Windows agent pairing as a separate path.

## 6. Database tables and API contracts

Create real schema/migrations (minimum): `tenants`, `users`, `roles`, `sessions`, `devices`, `licenses`, `plans`, `subscriptions`, `agents`, `mt5_accounts`, `symbols`, `telegram_sources`, `telegram_messages`, `signals`, `signal_revisions`, `signal_entries`, `order_intents`, `broker_orders`, `positions`, `deals`, `commands`, `outbox_events`, `risk_policies`, `risk_snapshots`, `trade_journal`, `notifications`, `audit_events`, `backups`, plus mandatory managed hosting records: `hosting_plans`, `managed_hosts`, `host_provisioning_jobs`, `worker_instances`, `worker_heartbeats`, `tenant_host_assignments`, `broker_connection_grants`, `secret_references`, `host_migrations`, `hosting_usage`. Every mutable trade/account record tenant- and broker-account-scoped; transactional unique keys for duplication. Legacy migration script provided with dry-run and rollback path.

Typed `/api/v1` routes for auth/onboarding, licenses, broker management, signal history, orders, positions, trade operations, analytics, risk settings, Telegram sources, backup manifests, provider studio and admin. Pagination, filtering, validation, authorization, rate limits, OpenAPI documentation, consistent typed error responses. Realtime events for broker heartbeat and order transitions. HTTP 200 only means command *accepted by API*, not broker accepted/fill.

## 7. Security and fail-safe requirements

- No MT5 login/password or Telegram session in browser bundle/localStorage/network logs; Windows secrets DPAPI + explicit consent.
- No plaintext auth keys or secrets committed to Git. Provide `.env.example` with placeholders, never real values.
- HTTPS, secure cookies, CSRF/CORS, RBAC, tenant authorization, MFA/2FA support, audit trail, signed agent command envelopes, replay protection, rotation and revocation.
- Risk, emergency stop, broker reject and license safety rules remain effective even if UI requests otherwise.
- Consumer-grade claims like guaranteed win-rate or guaranteed trade placement are prohibited. MT5 is broker-authoritative.
- Secure cloud backups with key management. Logs redact PII, credentials and Telegram verification codes.
- Threat model: unauthorized cross-client order, duplicated order after crash, edit applied to wrong ticket, cloud disconnect, stolen device, broker stale response, netting collisions, expired license while positions open.
- Build unit/integration/e2e tests for all threats and core workflows; configure CI.

## 8. Exact execution scenarios / acceptance tests

A) `GOLD BUY 4000 SL 3950 TP 4100`: eligible account → 2 BUY_LIMIT intents at adjusted 4000.99; both SL 3950; L1 TP 50 configured pips from 4000.99; L2 TP 4100; broker retcodes recorded.

B) Same signal new Telegram message ID or group → 0 new orders on same MT5 account; DIFFERENT MT5 account permitted according to enabled settings. Account-specific idempotency survives restart.

C) New signal missing SL and TP → 2 layers; shared fallback SL 50 pips; L1 TP 50 pips; L2 TP 150 pips.

D) Reply or edit “entry eka 4050ta ganna SL eka 4000ta tiyanna” → if original layers pending, update only correct tickets; adjusted Gold BUY 4050.99; shared SL 4000; L1 TP rebased; L2 TP retained original. Already filled entry not changed.

E) BUY_LIMIT above current Ask or SELL_LIMIT below current Bid → app does NOT silently market-price skip or convert to MARKET/STOP; submit intended LIMIT request; if broker rejects, show `BROKER_REJECTED` with real code.

F) Layer 1 quick TP hits → optional setting can move Layer 2 SL to BE, only if actual broker fill is confirmed. Disabled default means no automatic new action.

G) 2 MT5 terminals with separate brokers, one accepts and one rejects → correct independent status/tickets, no MAIN fallback.

H) App/worker crashes during `order_send` → reconciliation before new attempt; no duplicate pair after restart.

I) **DEFAULT MANAGED MODE:** Client has smartphone only, NO PC, phone switched OFF → platform-managed Windows MT5 worker continues processing signals while service healthy; dashboard shows `CLOUD_AGENT_ONLINE`, accurate broker and Telegram health. **OPTIONAL BYO MODE:** Client PC powered OFF → its worker shows `AGENT_OFFLINE`; never silently represent a client PC as required for managed mode.

J) Expired license → no new submissions, but safe manage/close/cancel/reconcile remains available.

K) 2 clients with different tenants → zero access to each other's broker/Telegram/trade data; API negative permission tests.

L) Backup restore → MT5 reconciliation first, then resume; no duplicate old signals.

M) Broker symbol `XAUUSDm`, different `digits` and pip model → normalization, price rounding, volume sizing, SL/TP calculated correctly according to explicit symbol map.

N) Netting account → 2 logical layers tracked with limitation clearly signaled; do not promise separate independent open positions if broker merges them.

All tests must be automated where possible (mock/fake MT5 response first), then a **separate explicitly labeled Windows + MT5 DEMO** verification checklist. Never place live trades as part of automated tests.

## 9. Build process: actual code, not a plan only

Follow these steps **without stopping at an architecture explanation**:

**Phase 0 – Source audit and preservation:** Extract ZIP; inventory modules; inspect configs and logo; capture owner rules as regression tests; identify conflicts from historical docs; make backups and migration map.

**Phase 1 – Working Web Foundation + Mobile-Only Onboarding:** Initialize monorepo; Next.js branded Web/PWA, Node API, PostgreSQL migrations, real auth, tenant/role separation, navigation and dashboard with read-only real API endpoints, Docker Compose local development; implement phone-only managed setup wizard and host provisioning state APIs with test adapter (clearly marked demo until cloud credentials configured).

**Phase 2 – Platform-Managed Windows MT5 Execution:** Implement real cloud host provisioner/IaC, isolated Windows worker image/bootstrap, phone-triggered worker allocation, secure broker grants/KMS, worker lifecycle + health + reconciliation. Support optional BYO pairing; no-PC onboarding is DEFAULT. Refactor legacy execution engine, per-broker worker and reconcilers, durable order intents and duplicate guard; preserve exact 2-layer LIMIT owner rules.

**Phase 3 – Telegram & Risk:** Real Telethon event ingestion, multilingual edits/replies, risk manager, expiry, BE/partial TP and live synchronization.

**Phase 4 – Analytics & Admin:** real broker deals, P&L, journal/report export, owner client panel, licensing/entitlement system, encrypted backups.

**Phase 5 – Productionization:** security tests, API e2e, mobile-only client onboarding E2E, managed Windows VM/host provisioning tests, real phone-off/worker-on demo verification, cost monitoring, secrets management, cloud deployment guide, Windows service packaging (internal managed + optional BYO), fresh install/upgrade/migration tests, client onboarding and demo acceptance.

At the end of every phase include: actual file paths created/modified, run commands, test results with pass/fail counts, remaining blockers and next phase. When a feature genuinely requires credentials or external services, complete local implementation and `.env.example`, leave only the external configuration step explicitly marked; don't fabricate integrations. If execution environment restricts file system/network or OS, produce the runnable project files you can generate and explicitly list unverified Windows/MT5 steps.

## 10. Final deliverables — mandatory

1. **Complete downloadable ZIP** of updated web project with all actual source code (not just an HTML mockup).
2. **Platform-managed Windows MT5 hosting** source + infrastructure-as-code/VM provisioning/Windows bootstrap/scripts, tenant isolation, health, secrets, billing usage and runbook; optional self-hosted connector package/installer and source. Client must NOT need their own PC to use managed plan.
3. One-command local dev start (`docker compose up -d` for services; `npm install`, `npm run dev` or equivalent) and Windows agent startup scripts; full Windows PowerShell instructions written simply in Sinhala.
4. PostgreSQL migrations, SQLite migration/import scripts, `.env.example`, demo seed data without real credentials.
5. Functional responsive web UI with real frontend↔API integration, proper loading/error handling, admin/client roles, mobile PWA.
6. Automated unit/integration/e2e tests, owner-rule regression suite, CI workflow, demo MT5 checklist and truthful test report.
7. Backup/restore runbook, licensing/admin guide, managed Windows cloud host provisioning/deployment + optional BYO Windows VPS guide, HTTPS/domain guide, cost model, uptime/failure behavior and operational observability.
8. **README-SI.md** with simple beginner-friendly Sinhala instructions: **phone-only user onboarding with ZERO PC/installer/VPS setup**, plus separate owner cloud hosting setup and optional advanced BYO PC guide; connect Telegram, connect MT5, test DEMO, launch web app, add client, issue license, restore backup, troubleshoot.
9. Migration checklist mapping old desktop modules/screens/settings to new web pages/services and a list of anything not yet implemented.
10. Release notes, known limitations, deployment prerequisites, and clear differentiation: `implemented + tested`, `implemented but not tested on Windows/MT5`, `requires external keys`, `not implemented`.

## 11. Output format & working style

Start your first response with a **short Sinhala source audit and proposed architecture**, then **immediately begin implementing Phase 0 and Phase 1 files**. Do not waste turns on generic advice, repeated confirmations, long introductions or asking me already answered questions. Use sensible defaults stated here. Do not ask for secrets in chat; use local `.env` instructions. If you cannot finish all phases in one response/session, give a working, honest phase deliverable and exact continuation plan; never say 'all completed' without code and tests.

**SUCCESS =** EdgeQuant brand තිබෙන real multi-user responsive web platform එකක් browser/mobile එකෙන් run වීම + **PC එකක් නැති client කෙනෙක්ට smartphone ONLY භාවිත කර signup → connect broker → connect Telegram → demo trade → enable live කළ හැකිවීම, platform-managed isolated Windows MT5 host එකකින් automation දිගටම run වීම** + optional self-hosted mode + owner 2-layer LIMIT/SL/TP/Gold offset/duplicate/edit rules preserve වීම + features 10 usable and verifiably tested + client license + managed hosting deployment workflow. **Pure screenshot UI, design mockup, placeholder-only API or untested live-trading claims are NOT success.**
