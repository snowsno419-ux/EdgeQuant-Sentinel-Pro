# EdgeQuant - AI Agent removed / editable Max Open Trades (2026-11-06)

## What changed

1. **Autonomous AI Agent feature is retired.** The AI Agent desktop page, sidebar entry, Dashboard management-note widget, ON/OFF/style controls and `/agent`/`--agent` command surfaces are removed. The open-position autonomous agent loop is hard-disabled, including when a frozen client's older saved settings contain `AGENT_ENABLED=true`. Dormant legacy helper definitions remain in the engine only for backward compatibility; they do not run.
2. **Other trading tools are NOT disabled.** Telegram signal execution, 2-layer entries, multilingual signal edits, login-code reuse, optional `AUTO_BE_ENABLED`, separate trailing stop, journal, broker dashboard and risk guards continue as before. `TRAILING_STOP` and AUTO BE are separate controls, not the retired agent.
3. **Max Open Trades settings are prominent.** Open **SETTINGS** -> **MAX OPEN TRADES / ORDERS**:

   - `MAX_OPEN_ORDERS`: total live+pending orders across the app; **0 = unlimited** (existing default).
   - `MAX_TRADES_PER_SYMBOL`: maximum LIVE running trades for each instrument; **20** is the new initial default (previously 6), **0 = unlimited**. This counts LIVE trades, not pending orders waiting to fill.
   - `MAX_PENDING_PER_SYMBOL`: maximum PENDING orders for each symbol; **0 = unlimited** (existing default).

## How to use on Windows / AWS

1. Stop EdgeQuant before changing settings or replacing the source.
2. Backup your existing application folder, journal, Telegram `.session` and local settings. Do NOT replace the `.session` or credentials with another user's files.
3. Extract this updated source ZIP and run `EDGEQUANT-APP.bat`. If using a compiled EXE, rebuild it with `BUILD-EXE.bat` and use the rebuilt EXE.
4. Open **SETTINGS**. At the top of the scroll area, find **MAX OPEN TRADES / ORDERS**. For example, set `MAX_TRADES_PER_SYMBOL` to `50`, optionally set `MAX_OPEN_ORDERS` to `100`, and leave `MAX_PENDING_PER_SYMBOL` as `0` if you want no app-side pending cap.
5. Click **SAVE SETTINGS** while the bot is stopped, then restart EdgeQuant. Frozen client builds persist settings in the current Windows user's local client settings; source runs edit `edgequant_auto.py`.
6. Test with a DEMO MT5 account before LIVE. Limits do NOT bypass MT5 broker margin, symbol, stop-distance, trade limits, market status or other acceptance rules. Two layers per entry mean a single Telegram entry can create two orders.

## Testing and limitations

- Targeted offline regression tests: **61 passed** across trading layer, multilingual edits, Telegram authentication and agent/limit controls.
- Virtual-desktop GUI smoke test passed: 16 tabs built, no AI Agent tab, all three limit inputs visible.
- Legacy full self-checks still have known outdated assumptions from older strategy changes: Desktop **320 passed / 4 failed**; Engine **510 passed / 46 failed**. Do not interpret them as full green validation.
- No real AWS/Windows MT5 terminal or Telegram live execution was tested in this environment. Test with DEMO first.

Run the new checks on Windows: `python test_trade_limits_ai_agent_removed_20261106.py`.
