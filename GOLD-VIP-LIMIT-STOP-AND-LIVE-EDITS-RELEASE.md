# EdgeQuant Sentinel — GOLD LIMIT VIP pending fallback + live edit patch

## Signal placement (GOLD LIMIT VIP only)

- Keep the established raw-signal entry adjustment: BUY **+0.99**, SELL **-0.90** in XAUUSD price units. No repricing or market-order fallback.
- At the *same adjusted price*, select a valid BUY/SELL **LIMIT** if possible; otherwise select the direction-matching **STOP** only if the broker Bid/Ask and minimum-distance requirements allow it. Otherwise log/reject the price rather than placing an invalid order.
- Each entry is planned with **two layers**: Layer 1 TP **+/-50 gold pips**, Layer 2 **the Telegram signal TP**. A two-entry range plans **four orders**. These are intended order counts, not guaranteed live broker fills. A broker can reject one or both; best-effort cleanup of unmatched pending partner orders is included.
- GOLD LIMIT VIP protective SL offset is **BUY signal SL +0.20** or **SELL signal SL -0.20** (GOLD *price units*, not necessarily a universal 'pip').
- Keep MAIN and all enabled added MT5 broker routing. Quotes/minimum distances/symbol mappings must be checked on each broker separately.

## Updates

- A Telegram edit to the original GOLD LIMIT VIP signal (`MessageEdited`) is linked by **the same chat ID and message ID** to journaled signal tickets. The original signal must still be complete and directionally valid.
- Signal TP edits affect **Layer 2 only**; Layer 1 stays fixed at 50 pips. SL edits can affect both layers. Entry edits affect **pending orders only**, preserving the original BUY/SELL entry offsets. A filled position's entry is never modified.
- Explicit replies in Sinhala, Singlish, or English can request TP/SL/entry changes when **directly linked** to the original signal. Ambiguous updates are logged and skipped; the system must never modify all XAUUSD positions on symbol match alone.
- Original result notices like `SL HIT` are not new trade actions.
- When the owner switches **Auto BE OFF**, autonomous BE triggers are disabled. The system does not interpret "BE after 50 pips" in the original text as automatic permission. Profit-protecting broker controls may still act independently according to their own configured settings.
- Original-edit application uses a durable receipt per distinct edited message body to suppress duplicate automatic order mutations after restarts. A failed/uncertain mutation is NOT automatically retried; inspect the journal and MT5.

## Running and limits

1. Extract the entire ZIP, keep the existing user configuration, and start `EDGEQUANT-APP.bat` from the extracted project folder.
2. Configure `GOLD LIMIT VIP` as a **LIMIT category** source, connect MAIN, and test additional broker terminals separately before enabling them.
3. Run `python -m unittest discover -p 'test_*.py' -q` and `python edgequant_auto.py --selftest` for offline checks.
4. Test on **MT5 demo accounts** with Telegram examples including range entries, pending STOP fallback, Auto BE OFF, and edited posts.

**NOT live-tested** in a Windows/MetaTrader 5/Telegram environment here. Real broker order acceptance, minimum distances, trade freezes, connection errors, and exact multi-account fill timing are not guaranteed. This is a Python source project, **not a Windows 7-compatible installer**. There is no promise that all pending layers can be placed or stay open when the broker rejects or changes market conditions. Avoid live funds until demo validation succeeds.
