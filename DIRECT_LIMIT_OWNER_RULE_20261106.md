# EdgeQuant — Direct LIMIT Owner Rule (2026-11-06)

This release updates **the source code**, not a running Windows EXE/AWS process. Existing pending/live MT5 tickets are not altered. A new Windows EXE must be rebuilt if the installed application uses a compiled distribution.

## Behavior

- When a parsed entry-bearing Telegram trade signal contains a valid BUY or SELL direction and an entry, use two **BUY_LIMIT** or **SELL_LIMIT** pending-order requests for **each** entry level (at most the existing `MAX_LEVELS=2` entry levels per signal).
- Use the **signal entry exactly** (no Gold +0.99/-0.90, no directional 10-pip shift, no Bid/Ask comparison or repricing), and do not convert a LIMIT to STOP or MARKET. Actual broker acceptance is determined by MT5. Orders are submitted immediately when the terminal and user-configured trading controls permit.
- Layer 1: fixed 50-pip SL and 50-pip TP from entry, regardless of the signal SL. Layer 2: supplied signal SL or 50-pip fallback, and supplied signal TP (the selected TP3/last target in a multi-TP signal) or 150-pip fallback.
- Preserve the established project pip sizes: Gold/XAUUSD 1 pip = 0.1 price units; standard forex 0.0001; JPY forex 0.01. This can differ from some brokers' display convention.
- The old missing SL/TP **manual-review** gate has been removed. The dashboard execution-review queue and confirmation buttons are no longer shown. A valid direct-limit plan submits each layer separately, recording confirmed tickets or broker rejection errors. One rejected layer does not automatically cancel the other.
- Explicit `BUY NOW`, `SELL NOW`, `ENTER NOW`, or `MARKET` trade messages stay on the existing MARKET path; management commands remain management commands. The existing risk/PAUSE, channel and broker switches, news, trading-hour, emergency-stop, and weekend restrictions still apply. Direct-limit signals bypass spread, stale-age and TP-already-hit filters, and do not use market price to decide a LIMIT type.
- When broker communication returns an *ambiguous* response (timeout/no receipt), sending stops until MT5 broker history is verified, to avoid double-filling a possible already accepted order. No silent auto-retry or manual-approval queue is used for direct-limit dispatch.

**No unconditional placement guarantee:** MT5/broker rules may reject pending LIMIT prices on the wrong side of the current market (`10015`), invalid SL/TP levels (`10016`), unsupported volume, account restrictions, closed markets, or invalid symbols. A broker rejection is a reported failure, not a successful placement. The app cannot bypass broker validity checks.

## Example, XAUUSD BUY LIMIT 4193 with missing SL/TP

| Layer | Pending type | Entry | SL | TP |
|---|---|---:|---:|---:|
| 1 | BUY_LIMIT | 4193.00 | 4188.00 | 4198.00 |
| 2 | BUY_LIMIT | 4193.00 | 4188.00 | 4208.00 |

For **SELL LIMIT 4193**, the missing-level defaults are layer 1: SL=4198, TP=4188; layer 2: SL=4198, TP=4178.

## Install & verify (Windows / AWS Windows)

1. Back up the existing installation folder and any user-specific `edgequant_state.json`, Telegram session files and brokers configuration. Stop the current running EdgeQuant process **before** replacing files; do not run two automated traders on the same account.
2. Extract the new ZIP to a new folder. Copy your existing *private* configuration, broker mappings, credentials and sessions as needed. **Do not overwrite your real account state with a different archive's old settings.**
3. On Windows PowerShell inside the extracted root folder, run `python -m unittest -v test_owner_direct_limit_20261106` (mock orders only). Then start `EDGEQUANT-APP.bat` for the desktop source, or rebuild the EXE using `BUILD-EXE.bat` if your installation runs an EXE.
4. Test **DEMO first** with one small BUY LIMIT and SELL LIMIT, including a signal missing SL and TP; confirm two pending ticket numbers and their actual entry/SL/TP in the MT5 terminal. Check broker's minimum stop distance and tick precision for the configured symbol.
5. No live MT5 or Telegram integration test was possible in the offline development environment; only fake-MT5 order dispatch and Python syntax checks were run. Do not assume an AWS deployment was changed just because the ZIP was generated.

## Sinhala summary

**BUY/SELL LIMIT signal එකේ entry එක වෙනස් නොකර**, එක entry එකකට pending LIMIT layers 2 යවයි. **Layer 1 SL/TP = 50/50 pips**, **Layer 2 signal SL/TP** තිබේ නම් ඒවා; නැති නම් **SL 50, TP 150 pips**. Missing SL/TP හේතුවෙන් manual-review queue වෙත යවන්නේ නැහැ. Broker එක order reject කළහොත් error එක පෙන්වයි. Actual pending ticket එකක් ලැබුණු විට පමණක් `pending` ලෙස සලකයි. MT5 broker limit-order rules bypass කළ නොහැක.
