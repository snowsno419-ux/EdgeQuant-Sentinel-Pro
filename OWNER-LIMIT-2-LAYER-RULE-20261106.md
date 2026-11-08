# EdgeQuant Owner LIMIT Order Rules — 2026-11-06

- Every parseable BUY/SELL signal with an entry creates exactly 2 pending LIMIT request(s) per signal entry for each selected/enabled connected MT5 broker. Distinct source entries each create their own pair.
- XAUUSD fixed entry adjustment from owner's prior rule: BUY = given entry + 0.99; SELL = given entry - 0.90 (price units, not current live broker spread). Other symbols use the supplied entry without Gold offset.
- MT5 order type is BUY_LIMIT / SELL_LIMIT. No live Bid/Ask comparison to suppress placement; no replacing the LIMIT with STOP or MARKET, and no chasing current market. Invalid orders may still be rejected by MT5/broker. A submitted request is **not** a confirmed trade until MT5 returns a confirmed ticket.
- Both Layer 1 and Layer 2 take the **same exact signal SL**. If absent, both take the same calculated protective 50-pip SL from the adjusted entry. No +0.20/-0.20 SL adjustment.
- Layer 1 TP is 50 pips by default, changed live on the Dashboard via **LAYER 1 QUICK TARGET**; per-provider override (where present) is honored.
- Layer 2 TP uses the selected signal TP exactly; when absent it uses 150 pips from adjusted entry.
- If LIMIT is rejected, record MT5 retcode and comment; no manual-review pre-check and no silent alternate order type. If MT5 result is ambiguous / times out, stop to avoid duplicate exposure and require ticket reconciliation.
- Screenshots show pre-rejection, stale/price gate, a legacy malformed journal JSON line, and a hidden NameError. Changes address pending-price gates and malformed journal rows; the detailed NameError stack is now logged for exact diagnosis.
- Existing emergency stop, account/channel on/off, position limits, market closure and other non-price safeguards remain in force. The broker cannot be compelled to accept invalid LIMIT prices. Test on **DEMO** before using any LIVE credentials.
- Stop EdgeQuant, back up settings/journal/Telegram sessions, extract ZIP, and run `EDGEQUANT-APP.bat`. For the EXE use `BUILD-EXE.bat` to rebuild. Do not copy old Python files back over the updated ones.
