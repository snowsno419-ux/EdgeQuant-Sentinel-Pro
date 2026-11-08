# Engine Integration Step 7 — Pending-order preflight

Added `hybrid-desktop/bridge/order_revalidation.py`: fail-closed, read-only MT5 pending-order validation for fresh Bid/Ask, spread maximum, broker tick size, stops/freeze levels, order direction, SL/TP and emergency-stop state. Returns explicit reasons without changing entries or order types.

IMPORTANT: This is an isolated validation library, not wired into approval/execution. Manual Review Approve remains disabled. It does not verify MT5 trade mode, filling mode, available margin, symbol aliases, volume, quote timestamp, or atomic stop checks at the final order-send boundary. These must be integrated and verified before enabling execution. No live trades were placed.

Tests: `cd hybrid-desktop/bridge && python -m unittest -q test_order_revalidation.py` (9 passed on this environment).
