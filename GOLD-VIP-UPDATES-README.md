# GOLD LIMIT VIP — Exact-linked updates

The VIP channel-specific parser supports new LIMIT signals and these follow-up categories:
- Direct Telegram replies: explicit **BE**, **cancel entry**, **close** instructions may be automatically applied to **only** the original signal's recorded broker tickets, if all safety gates pass.
- BE follows the owner's Auto BE enabled/trigger and selected-layer rules; only eligible profitable positions are changed.
- Cancel entry affects only still-pending tickets; close affects only recorded open tickets.
- HOLD, SL HIT, entry-price changes, commentary, edited messages without a safe original linkage, ambiguous updates and comments posted in a separate discussion chat are logged/blocked; no broker mutation.
- Quoted messages are not treated as new signal orders.
- A durable intent and audit record are written before any broker action; uncertain attempts are not retried automatically.
- No symbol-only matching. Channel ID + original Telegram message ID + broker ticket required. The Telegram channel must be configured as LIMIT.

**Important:** This is source-level integration. Not tested against a live Windows MT5 terminal or Telegram group. Test with a demo account and review logs, especially reply IDs and broker ticket attribution. Existing trade management functions are reused; no new broker-side SL/TP logic is invented.
