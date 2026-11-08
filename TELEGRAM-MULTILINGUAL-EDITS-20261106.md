# EdgeQuant Telegram Signal Edit / Reply Auto-Updates — 2026-11-06

## What changed

`edgequant_signal_updates.py` is a pure-Python parser/planner connected to the existing `edgequant_auto.py` Telethon listener. No Telegram account/API keys are hardcoded in the new module.

1. **Original post edits:** `events.MessageEdited` updates tickets journaled with the exact original `(Telegram chat ID, message ID)`, across brokers, for general LIMIT channels as well as GOLD LIMIT VIP.
2. **Direct replies:** A new Telegram message that replies to an original signal can update its pending entry, SL and TP, even if the message is English, Singlish or Sinhala. No new trade is created for a matched modification.
3. **Unthreaded modifications:** Only if the follow-up quotes the *OLD* source entry and **exactly one** active original signal in the same Telegram chat matches. No guessing by latest signal or GOLD alone.
4. **GOLD shorthand:** `මේක ගන්න 24.25 ගනේ`, replied to an original GOLD BUY at 3925, means 3924.25 source entry if this is the unique nearby interpretation. Unknown/ambiguous shorthand is not submitted.
5. **Two layers:** An entry edit moves both **pending** layers. L1 quick TP is recalculated using the Dashboard's `LAYER1_TP_PIPS` (default 50), and L2 keeps the original signal TP unless the follow-up explicitly changes TP. A changed SL is applied to **both layers**. TP edits affect only L2.
6. **Prior Gold entry adjustment retained:** For tickets originally submitted at BUY +0.99 / SELL -0.90, the update retains that same stored adjustment. Non-GOLD symbols retain their own original entry scaling. Existing levels are not forcibly changed based on a fresh market quote.
7. **No duplicate application:** Write-ahead `edgequant_scoped_edit_receipts.jsonl` records each edited message/reply by its unique digest before MT5 modifications. The app does not blindly replay an uncertain broker response.
8. **Broker-confirmed change:** `TRADE_ACTION_MODIFY` for pending orders or `TRADE_ACTION_SLTP` for open positions, using recorded broker + ticket, expected symbol, direction and magic. Only **confirmed** edits update the journal. Broker invalid price/stops responses are logged; no fake success.
9. **Already filled:** A live position's entry cannot be moved. On a pending-to-filled race, the handler attempts only valid SL and (L2) TP adjustments while leaving the fill entry and L1 quick TP unchanged. Existing protected BE/profit-lock stops are not loosened.

## Examples

Original signal:

    GOLD BUY 4000
    SL 3950
    TP 4100

Direct reply to *that* Telegram message (three accepted styles):

    Move entry to 4050 and SL to 4000
    entry eka 4050ta ganna SL eka 4000ta tiyanna
    මේකේ entry එක 4050ට ගන්න SL එක 4000ට තියන්න

For the original tickets using +0.99 Gold entry adjustment, the new pending entry is 4050.99 for both L1/L2, both SL 4000, L1 TP 4055.99, L2 TP unchanged at 4100. All updates can still be rejected by MT5 if broker-side rules make them invalid.

Another unthreaded pattern that can match uniquely:

    From 4000 to 4050, SL 4000

The screenshot-format GOLD LIMIT VIP text (original edited message) is supported:

    GOLD BUY 3923 SL 3916 TP 3959 (or You can BE on 50 Pips)
    මේක ගන්න 24.25 ගනේ

This only infers 3924.25 from a uniquely matched original GOLD source price near 3923; it is not a general permission to guess incomplete prices.

## Important limits

- MT5 cannot be forced to accept a BUY_LIMIT above the permitted quote, a SELL_LIMIT below the permitted quote, or an SL/TP violating broker stop/freeze levels. The update is sent **without a client Bid/Ask rejection gate** but MT5 may reject it.
- A filled position's **entry** never changes. It requires a new trade, which this update handler intentionally does not create.
- Avoid automated edits from ambiguous messages like `aye buy ganna epa`, `hold if you want`, and SL/TP HIT outcome notices. These are not unambiguous numeric entry edits. Existing management handlers remain responsible for clearly scoped cancel/close/BE requests.
- Not all possible Sinhala/Singlish phrases are recognized. Only patterns clearly identifying a numeric field and matching exactly one source ID/entry are automatic. Unlinked or unclear instructions cannot safely choose a ticket.
- Event-based `MessageEdited` listening requires an active Telegram connection. An edit that occurred while offline may not replay automatically, unlike new-message catch-up; compare Telegram with MT5 manually after a disconnection.
- Never automatically modify tickets under a different Telegram chat, broker, symbol, direction or magic number.

## Deploy without losing settings

1. Stop the desktop app and MT5 execution engine first; make an external copy of the whole current folder, especially state, journal, session files, and private broker configuration.
2. Unzip this source ZIP into a **new** working folder (do not run two copies simultaneously). It deliberately excludes local runtime state files (`edgequant_state.json`, logs, sessions). Copy your personal settings and journals from the backed-up installation into the extracted folder only as needed.
3. Install any required dependencies from the included `requirements.txt` and run `EDGEQUANT-APP.bat`. For the packaged Windows EXE, run `BUILD-EXE.bat` first.
4. Test with a **Demo MT5 account** and a test Telegram channel; post a full entry and reply directly to it with an entry + SL update. Confirm **both** MT5 pending tickets, broker names, adjusted entry, SL, L1/L2 TP and journal records.
5. To test parser/MT5 requests offline (no real trades), run `RUN-TELEGRAM-EDIT-TESTS.bat` on Windows, or `python -m unittest test_scoped_multilingual_signal_updates_20261106 test_multilang_engine_dispatch_20261106 test_owner_direct_limit_20261106`.

### Regression compatibility note

43 focused offline tests pass (23 parser/planner + 6 dispatch/mock MT5 + 14 owner direct-LIMIT tests). Three unrelated legacy expectations in the old full regression set still disagree with the **previously requested** LIMIT-only/relaxed parser rules: two tests expect STOP fallbacks instead of the owner's LIMIT-only behavior, and one expects an invalid result for a format that the current parser recognizes as a candidate signal. Those legacy tests are retained as-is for transparency, not silently modified. This package has **not** been exercised against a real Windows/AWS MT5 terminal or live Telegram stream.
