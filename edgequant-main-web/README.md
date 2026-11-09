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
