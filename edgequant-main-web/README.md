# EdgeQuant Sentinel Pro — canonical main web demo (Phase 8F)

This folder is the **main dashboard UI** from the Limit Order Automation Rules project, not the detached daily-risk micro demo.

## Deploy
- Vercel project: `edgequant-sentinel-pro-demo` (existing)
- Root directory for future Git integration: `edgequant-main-web`
- Project framework: Other / static site
- Entry: `index.html`
- Telegram sample page: `telegram-demo.html`
- Local browser support: HTML + vanilla JavaScript; no build step.

## Visible features
- Receiver dashboard and sidebar, broker cards, sample trade animations, Telegram sample UI
- Browser-only daily profit/loss progress cards, broker/global selection, daily archive
- Sample Telegram signal simulation blocks new simulated trades on profit/loss limit hit

## Security / integration
This is a **public simulated UI**. It **cannot** enforce a broker's orders. Private Phase 8F API and Windows DEMO MT5 worker implement a separate, *source-only* pre-send gate; the private API, database, broker telemetry and Windows worker are **not connected to this Vercel site**. Do not use the simulation as evidence of real MT5 protections.

Current Vercel deployment was made manually through the API. Automatic GitHub-to-Vercel deployments require the Vercel user to authorize a GitHub Login Connection and link `snowsno419-ux/EdgeQuant-Sentinel-Pro` to the Vercel project with this root directory. Do not store Telegram sessions, broker passwords or API tokens in this public repository.

Run a real **DEMO MT5** end-to-end test before enabling any automatic broker orders. Protective SL/TP updates and existing position management must remain permitted while blocking new opening orders.

## Phase 8G — Mobile receiver dashboard (2026-11-09)
- Mobile topbar wraps on narrow screens (320–740 px) without horizontal scrolling.
- Bottom navigation: Home, Live, Risk, Signals, More. More has overlay, close button and Escape support.
- Two broker risk cards show **sample** broker P&L and browser-only limit-hit status; tapping opens the matching Daily Limits view.
- The compact mobile "Live Position Pulse" reuses the original animated trade monitor (4 rotating sample positions); no second trading feed or order executor.
- Simulated daily profit/loss progress, archive and Agent demo logic remain from Phase 8F.
- Local Chromium smoke tests: 10 responsive widths (320–1440 px), zero page errors; verified 5-second rotation, broker tap navigation, loss-hit gate false, menu open/close and Live tab.
- Vercel canonical project manually deployed with READY status. GitHub auto deployments **are not linked** until the owner authorizes the GitHub login connection in Vercel.
- **No real MT5 worker, Telegram account, broker telemetry, or production order enforcement is hosted by this static public demo.** Real Demo MT5 end-to-end tests remain required.
