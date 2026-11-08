# Engine Integration — Step 1 (read-only)

Added `hybrid-desktop/bridge/engine_audit_adapter.py` to read the **real existing** `edgequant_signal_audit.jsonl` and `edgequant_signal_review.jsonl` produced by `edgequant_auto.py`. It produces the existing bridge's `edgequant-signal-monitor` JSON status format. It does not place orders, start the engine, expose Telegram message text, or authorize trading.

Example (run from project root while original engine runs independently):

`python hybrid-desktop/bridge/engine_audit_adapter.py --project-root . --output hybrid-desktop/signal-status.json`

Configure `EDGEQUANT_SIGNAL_STATUS_FILE` for the bridge to point to that output file. The existing bridge `/status` endpoint can then show actual audit-based signal counts and pending review count. Pending review count is derived from append-only review records; final status accuracy depends on whether the existing engine writes resolution records to that file. The adapter is not a live execution connector.

Tests: `cd hybrid-desktop/bridge && python -m unittest discover -p 'test_*.py' -q` -> 27 tests passed in this environment.

Not yet verified: running engine in Windows, live MT5, Telegram sessions, emergency stop, frontend packaging, installer.
