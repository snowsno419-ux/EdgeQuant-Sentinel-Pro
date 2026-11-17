# EdgeQuant Option B — Premium Broker Risk Control Hub (2026-11-17)

Scope: visual system-wide redesign, using Desktop v2.0.4 source as brand/trading-rule reference.

## Web/Mobile (staged read-only)
- Shared design tokens applied to Login, Dashboard, Brokers, Telegram Channels, Studio, Journal, Calendar, Settings, responsive navigation and standalone recovery/verification pages.
- One dedicated broker card per registered MT5 DEMO account; signed balance/equity/floating and separated Daily Loss, Daily Target and Floating Exposure progress.
- Risk drafts are account-ID and verified-user-ID scoped in browser localStorage. SAVE DRAFT does not change server policies or execute trades.
- IMPORTANT: Current Vercel signed DEMO telemetry does not report account currency or daily trading net. Daily Loss/Target remain UNAVAILABLE. Floating exposure is labelled partial.
- No fabricated profit, orders, broker passwords, Telegram OTPs or active cloud trading.

## Desktop (separate offline working source, not in this PR)
- Shared SENTINEL PRO palette becomes first theme for new installs, existing themes remain.
- Broker cards with separate per-account daily protection and progress bars, bound to exact broker label/login/server, in account currency.
- New order gates check broker trading deals plus floating P&L; unavailable data fail closed for enabled account protection. Existing positions never auto close. Global emergency stop and old global loss limits remain independent.
- Broker risk policies stored in user-writable Windows LocalAppData rather than Program Files.

## Status
Keep draft. No production merge or paid services. Windows installer and real DEMO tests still required.
