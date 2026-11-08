# EdgeQuant Sentinel integration release status

This is **not a completed or live-trading-ready build**. Do not use a real-money account.

## What exists
- Electron/React desktop source, Python engine, local bridge, Telegram parser, review queue.
- Approval transport and engine consumer; consumer intentionally quarantines approvals **without sending orders**.
- Duplicate claim, preflight and broker reconciliation modules, plus a read-only MT5 history adapter (`hybrid-desktop/bridge/mt5_history_adapter.py`).
- The history adapter does not call order_send and does not claim absence of records proves absence of execution.

## Critical remaining integration
1. Safely connect review approval to actual engine execution with durable broker intent and recovery semantics; existing consumer quarantines instead.
2. Wire the read-only history adapter into engine lifecycle and verify broker comment tagging end-to-end. MT5 brokers may modify comments, so missing matches require human investigation.
3. Verify Electron controls, local authentication, emergency stop coverage and frontend build on Windows.
4. Run MT5 demo-only end-to-end tests on the user's Windows machine and produce the Windows NSIS installer there.

## Windows build (source only)
In PowerShell from `hybrid-desktop`:

```powershell
npm install
npm run build
npm run dist:win
```

`dist:win` requires a valid `bridge-build/edgequant-bridge.exe` resource. A build is **not** proof that MT5 execution is safe. Keep the approval button disabled until demo acceptance tests pass.
