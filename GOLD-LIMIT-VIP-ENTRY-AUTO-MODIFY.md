GOLD LIMIT VIP — pending entry auto-modification

A new explicit entry update (e.g. `Change entry to 3912`, `Entry 3912`) is acted upon only when the Telegram message directly replies to the original signal, the channel is GOLD LIMIT VIP configured LIMIT, and a uniquely linked pending order ticket and broker are recorded in the trade journal. The same XAUUSD adjustment applies: BUY +0.99, SELL -0.90. Pending orders are edited via MT5's ticket-specific modify action; MT5 broker validation may reject the edit.

Already filled positions, unmatched updates, updates without a single explicit price, and non-GOLD tickets are not modified. The existing durable intent audit prevents blind retries after uncertain broker outcomes. This is untested against a real Windows MT5 terminal; test with a demo account first.
