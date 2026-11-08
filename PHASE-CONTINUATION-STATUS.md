# EdgeQuant Sentinel — telemetry safety patch

- Reject missing, NaN, infinity or invalid MT5 quote timestamps instead of treating potentially stale quotes as live.
- Reject non-finite snapshot timestamps in the local bridge.
- Added regression tests for missing/non-finite quote timestamps.
- This is source-only; Windows MT5 connection, Telegram, live execution, emergency stop and installer are NOT verified.
