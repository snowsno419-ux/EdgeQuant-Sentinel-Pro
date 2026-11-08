# Step 14 — Read-only broker reconciliation evidence

Added `hybrid-desktop/bridge/broker_reconciliation.py` with `reconcile_snapshot`.

- Accepts **caller-supplied** MT5 order/deal snapshots and matches only explicit exact `review_id` tags.
- Persists observation and sanitized ticket evidence in SQLite `approval_reconciliation`.
- Does **not** change approval command states, place orders, or permit automatic retries.
- Missing broker connectivity, absent matches, and multiple matches all require human inspection. `NO_EXACT_MATCH` is **not** proof that a trade did not execute.
- No MT5 polling/connection, broker-history ingestion, crash recovery workflow, UI display, or demo-account execution is wired yet. Broker records must carry an explicit trusted review ID for correlation; existing MT5 orders may not have it.
- Automated bridge tests: 73 passed in the build environment. Some existing SQLite resource warnings remain.

This project remains **NOT FOR LIVE TRADING**.
