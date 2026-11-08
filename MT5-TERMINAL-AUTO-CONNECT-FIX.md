# MT5 Terminal Auto-Connect Fix

When MAIN has no explicit terminal path, desktop account polling, broker selection and history now prefer the MT5 terminal already logged in on the Windows desktop. This prevents a stale saved MAIN password/server from replacing a working session during read-only refresh.

If the terminal is not logged in, existing saved-credential fallback remains. Explicitly configured multi-broker terminals retain their existing path-based behavior.

No credentials are added, changed or deleted. No orders are submitted by this patch. Trading engine changes are restricted to the MT5 session-selection function. Verify on a Windows MT5 demo account before enabling auto trading.

Run `EDGEQUANT-APP.bat` with the MT5 terminal open and logged in. If the app reports -6 Authorization failed, check MT5 login and saved account routing. If -10004 No IPC connection persists, verify terminal installation, process permissions and that the correct terminal is open.
