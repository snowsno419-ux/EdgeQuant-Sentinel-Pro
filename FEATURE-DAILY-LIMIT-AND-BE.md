# Daily LIMIT report + per-layer automatic break-even

## Dashboard
Click **REFRESH TODAY'S LIMIT HISTORY** to query the currently selected MT5 terminal/account. Broker-confirmed entry deals are **TRIGGERED**. Fully unfilled, canceled/expired orders are **NOT TRIGGERED**. Still-open orders placed today are **WAITING**. Ambiguous history rows are **UNVERIFIED**, never guessed. Counts are per broker account currently connected, not aggregated across all broker accounts. The date boundary uses the Windows local clock; verify server timezone when auditing near midnight. MT5 history API and terminal connection required.

## Automatic break-even
Dashboard execution controls now have **BE LAYER**: `SIGNAL` (default, layer 2 signal TP), `QUICK` (layer 1 quick TP), `ALL` (both). Master **AUTO BE ON/OFF** and trigger pips remain separate. Automatic BE in the position manager only touches tickets whose layer was recorded during confirmed order placement in the current engine session. Unknown tickets are skipped rather than modified. **After restarting the engine, existing tickets have no restored layer mapping and will not receive auto BE** until the corresponding orders are newly recorded; do not assume protection. BE logic uses existing profit-only and broker SL validation. This change does not alter user-initiated manual SL edits.

## Verification
Python syntax checks and focused synthetic unit tests pass. Live broker reconciliation, UI rendering and actual order SL modifications have not been tested on Windows/MT5. Use demo trading first. No claim of production readiness.
