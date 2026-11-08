# Engine Integration Step 4 — partial safety implementation

- Added `hybrid-desktop/bridge/review_commands.py`: append-only rejection of pending review entries with fsync; no MT5 execution.
- Added `/review/approve` fail-closed response (409); approval cannot execute orders until an engine-owned revalidation and authorization protocol is built.
- The emergency stop from Step 3 remains configured via `EDGEQUANT_EMERGENCY_STOP_FILE`. Set this **identical absolute path** for the bridge and the engine process; do not treat the latch as cancellation of existing broker orders.
- Existing execution paths have not been comprehensively audited for bypasses. Desktop control wiring, authenticated review identifiers, cross-process locking, real broker integration, and installer are not complete.
- Test command: `cd hybrid-desktop/bridge && python -m unittest discover -p 'test_*.py' -q` (34 tests passed in this environment).
- No live trading validation was performed.
