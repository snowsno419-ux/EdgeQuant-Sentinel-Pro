# EdgeQuant Sentinel Pro — Mobile + Web Public UI Demo

**DEMO ONLY. NO LIVE TRADING.**

This folder contains the existing responsive Phase 3 standalone HTML UI preview, adapted for safe publication via GitHub and Vercel. It uses fictional sample balances, broker names, event data, and in-memory UI settings. The public page contains NO real authentication, connected Telegram, MT5 terminals, cloud broker execution, or customer records. Do not enter passwords, real account numbers, Telegram tokens, or worker secrets.

Vercel settings: link this Git repository, select Root Directory `mobile-web`, framework `Other` (static), no build command. Deployment output is this folder's static files. The app supports desktop sidebar and mobile bottom navigation, plus optional home-screen installation from manifest on HTTPS.

The Phase 3.1 development API and Windows read-only MT5 worker remain local-only prototypes and **MUST NOT be copied into this public static deployment**. Production authentication, secure backend, tenancy, worker provisioning, HTTPS transport, audit logs, and real DEMO MT5 testing are separate milestones.
