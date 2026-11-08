# Auto-placement / Manual Review fix

- Gold LIMIT orders with a valid pending entry, unchanged signal SL/TP and valid broker constraints still proceed automatically through the existing MT5 execution path.
- Gold LIMIT layers with invalid entry side or original SL conflict are now marked REJECTED instead of being added to the execution Manual Review queue. **They are not placed**. No silent repricing or conversion to STOP/MARKET.
- MT5 retcode 10027 (AutoTrading disabled by client) now fails without a comment-free retry.
- Excel report `ws2` sheet initialization fixed for short equity histories.
- Existing Manual Review features remain available for other ambiguous/unsafe cases. Old queued review items are not automatically deleted.
- This update has not been run against a Windows MT5 demo account. Use demo-only for validation; enable Algo Trading in MT5 if you want orders submitted.
