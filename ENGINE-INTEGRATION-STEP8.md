# Engine Integration Step 8

Added `hybrid-desktop/bridge/engine_order_preflight.py`, a broker-backed, fail-closed, read-only MT5 pending-order preflight. Checks current tick freshness, symbol visibility/trade mode, broker spread, tick size, entry direction, stop/freeze distances, SL/TP and volume steps. No order execution is authorized, and no approval status is changed. The existing `/review/approve` endpoint remains disabled until review record mapping, shared emergency-stop path, per-order execution gate, and MT5 demo tests are complete.

Tested: `python -m unittest discover -p 'test_*.py' -q` in bridge: 51 tests passed. No Windows MT5 session, frontend compilation, or installer verified in this environment. Never use for live trading.
