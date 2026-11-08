# Engine Integration Step 9 — engine-side broker preflight

The existing Python `execution_review_execute(review_id)` now runs `execution_review_preflight` before invoking the existing `execute_plan` path. It checks the exact pending execution-review row, external stop latch, MT5 symbol info, fresh broker tick, lot constraints, price/SL/TP direction, tick alignment and configured pip-based spread guard. Failed preflight leaves the review pending and does not submit orders. The original execution path repeats its existing broker checks.

**Not implemented:** Electron `/review/approve` remains deliberately disabled. The Telegram JSONL signal review queue and the engine's `edgequant_execution_review.json` are separate queues. There is no secure engine command transport yet, and no Windows demo MT5 end-to-end verification. This package is NOT live-trading ready.
