# Phase 8A — Premium Receiver Dashboard + Broker Performance + Smart Risk + Journal

**Status 2026-11-08: Public UI DEMO only.** Live site https://edgequant-sentinel-pro-demo.vercel.app

The complete self-contained HTML preview is committed on this branch:
`webapp/demos/receiver-premium-phase8a/index.html`

## Features and browser tests
- Receiver only: Signal Studio removed (Provider role remains separate).
- Broker-wise demo cards display account/server, sample Bid/Ask and spread points, realized P&L over selected period, sample floating P&L snapshot, open/pending counts. Unknown broker has no fake quote.
- Portfolio separates period-filtered realized from current open floating and labels the combined number.
- Capital/risk planning with example profiles, daily/weekly loss budgets, risk/trade %, max trades, max opens, loss streak. Browser-local storage only; no actual risk lock.
- Journal filter by broker/channel/exit period; the user's supplied 7-page journal style inspired the logo-branded, dark-gold multi-page report generated in browser. Seven report sections plus paginated detailed trades.
- XLSX export: five sheets including Broker Performance; journal filtering is preserved.
- Profit Calendar original hover/tap → Journal preserved.
- Browser verified desktop + mobile, sample broker insertion and N/A quotes, risk plan, downloaded PDF with embedded EdgeQuant image (10 pages for sample month) and real XLSX ZIP structure with 5 worksheets.
- Pure broker snapshot/risk guard offline Node tests: 9/9 pass. Source + tests + migration supplied in companion Phase8A ZIP attached in conversation.
- `011_broker_analytics_snapshots.sql` is an **unapplied migration proposal** for future account-verified read-only telemetry.

## NOT implemented
- Real MT5 worker quote ingestion; broker live Spread/Floating/Realized data; account-currency conversion; actual PostgreSQL migration; persistent cloud Journal; signed multi-tenant export; risk-limit server enforcement; live trade controls; production E2E/security.
- No Demo/Risk UI toggle can stop or permit a real trade.
- All values on deployed UI are synthetic. Any server integration must fail closed on stale quote or worker disconnected, and use booked deals for realized (including commissions/swaps), open positions for floating, and separate each broker's account currency.
- Telegram 2-layer BUY +0.99 / SELL -0.90 and Telegram-only LIMIT→STOP logic unchanged.

## Next Phase 8B
Implement authenticated worker analytics snapshots, secure tenant isolation, real broker-wise P&L/read-only journal import, timestamped bid/ask streaming, export services and risk enforcement with DEMO end-to-end testing.
