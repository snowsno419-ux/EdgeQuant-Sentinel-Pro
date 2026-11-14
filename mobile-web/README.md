# EdgeQuant Sentinel Pro — PC-inspired Mobile + Web UI

This is a responsive static UI adaptation of the actual EdgeQuant Neon Dark Pro 2.0 Windows desktop menus and dashboard labels, **NOT** a copy of the Windows trading engine. Source reference: `edgequant_desktop.py` from the owner-supplied 2026-11-13 v2.0.4.1 source package and its offline 1366×768 preview.

## Screen coverage
Dashboard, Channels, Brokers / MT5, Trade Journal, Channel Progress, Manual Trades, Profit Calendar, Trading Plan, Local Profile, Signal Studio, Advanced, Signal Preview, Activity, Settings, Guide and Workspace Setup. Mobile users get a bottom navigation plus accessible full side rail; desktop gets the familiar Neon Dark header, sidebar and controls.

## Safety and current limitations
This is a **public UI DEMO only**. No broker connection, trade execution, Telegram login, cloud auth, tenant database or payments are connected. Live balances and prices intentionally show em dashes. START is disabled; TEST RUN affects only the browser label. Local controls are *drafts saved in browser localStorage only* and have no effect on live trading. Never enter passwords, OTPs, Telegram session strings, real account IDs or secrets.

Production requires secure cloud backend, per-tenant provisioning, Windows MT5 workers, encrypted secret management, audited API actions and DEMO acceptance testing. Existing Windows execution/desktop source is neither embedded in nor published by this folder.

## Deploy
Vercel Git project `edgequant-mobile-web`, repository `snowsno419-ux/EdgeQuant-Sentinel-Pro`, `main` branch, **rootDirectory** `mobile-web`, framework `Other`/static, no build command. HTTPS domain is `https://edgequant-mobile-web.vercel.app`.
