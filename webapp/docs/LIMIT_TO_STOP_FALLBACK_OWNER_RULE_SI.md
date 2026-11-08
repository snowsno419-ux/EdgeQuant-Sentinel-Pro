# EdgeQuant Sentinel Pro — New owner rule: LIMIT → STOP fallback (2026-11-08)

## Trading rule (Telegram signals only)
- Original BUY_LIMIT/SELL_LIMIT request is sent to MT5 without any local Bid/Ask based pre-skip.
- Only on an *explicit, definite* broker rejection (`10015 INVALID_PRICE`, `10016 INVALID_STOPS`, or `10035 INVALID_ORDER`) evaluate STOP at **the same entry**.
- BUY_LIMIT → BUY_STOP, SELL_LIMIT → SELL_STOP. Keep SL, TP, volume, magic and per-leg order identity unchanged. Keep two independently tracked Telegram layers.
- Price geometry: BUY_STOP above current Ask + minimum stop distance; SELL_STOP below current Bid - minimum stop distance.
- Require STOP order support by broker, trusted fresh bid/ask/point and successful native `mt5.order_check()`; stop fallback disabled if these checks cannot be verified.
- Re-query broker orders/positions/history before second send and revalidate correct DEMO account. If outcome uncertain, **UNKNOWN_RECONCILE** and **NO automatic retry**.
- Do NOT convert for insufficient funds, market closed, disconnected account, ambiguous send, unknown broker response or other unrelated errors.
- Broker success/failure recorded with original LIMIT rejection code and actual pending type in order ledger; still subject to broker acceptance, margin and slippage.
- **This rule applies to Telegram source mode only**. Direct Provider-to-Receiver MT5 copy preserves the provider's original order type.
- Existing owner Telegram XAUUSD entry offset BUY +0.99/SELL -0.90, two layers, shared SL and TP1/TP2 remain unchanged.

## Implementation status / provenance
The source implementing this rule is in the ChatGPT conversation ZIP:
`EdgeQuant_Sentinel_Pro_Phase4_LIMIT_to_STOP_Fallback_20261108.zip`.
Its Python demo worker, Node ACK validation, SQL migration 004, UI ledger display and tests were implemented in that ZIP.

Tests: 9/9 domain Node + 55/55 backend Node + 37/37 worker mock Python = **101/101 offline passes**. Windows real-demo broker verification, PostgreSQL integration, and full frontend/backend production builds are **NOT VERIFIED**. The ZIP is NOT a finished live cloud trading system.

**Important:** This GitHub branch is a milestone documentation/schema checkpoint and is **NOT** yet a complete synchronized copy of all changed ZIP source files.
