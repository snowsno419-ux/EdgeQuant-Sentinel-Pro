# GOLD VIP channel-specific parser — safe staging

Added `edgequant_vip_format.py` with 10 unit tests. This module is a **pure parser**, not an MT5 execution hook. It is disabled for every channel unless its numeric Telegram channel ID is explicitly passed in `enabled_channel_ids`.

Examples recognized: GOLD BUY 3901 SL 3895 TP 3924; GOLD SELL 3997-4002 SL 4007 TP 3969; GOLD BUY 3945-3942 SL 3936 TP 3996; optional BE on 50 Pips advisory; Sinhala/English hold, close, BE, entry updates, and SL-hit notices.

The screenshots do not provide reliable Telegram message IDs, reply-to links, channel ID, or edit events. Updates are therefore classified but **not automatically executed**. `resolve_update()` requires a real Telegram reply_to_id matching a recorded original signal ID. In production, edited-message handling must reconcile original message IDs and journaled broker tickets, then check the exact account/position and SL/TP constraints. No action should be taken on ambiguous updates. The parser does not decide LIMIT vs MARKET solely from the group name or the quoted header. Actual order-type selection needs broker bid/ask and validated execution rules.

Integration needed: wire to the existing Telegram event path only after the exact numeric channel ID is supplied and matching/reconciliation with MT5 tickets is tested on a demo account. Do not enable live execution based solely on these screenshots.

Run tests: `python -m unittest -q test_edgequant_vip_format.py`.
