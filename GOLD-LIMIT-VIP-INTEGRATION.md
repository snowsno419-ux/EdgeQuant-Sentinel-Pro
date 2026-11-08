# GOLD LIMIT VIP integration — guarded first release

This release wires `edgequant_vip_format.interpret` into the original Python engine's `handle_signal` entry point, **only** when Telegram chat title exactly equals `GOLD LIMIT VIP` (case-insensitive). The channel must be configured as LIMIT. Other channels continue using the original parser.

Supported candidates: `GOLD BUY 3901 / SL 3895 / TP 3924`, `GOLD SELL 3997-4002 / SL 4007 / TP 3969`, and buy entry ranges. Valid candidates are passed to the existing MT5 broker quote, spread, stop-level, and pending-order preflight path, which already applies BUY +0.99 and SELL -0.90 for Gold LIMIT. It does not convert a rejected LIMIT order to a MARKET/STOP order.

**Safety limitation:** Sinhala/English HOLD, CLOSE, BE, SL-hit, quoted signal commentary, edits with ambiguous intent, and entry-change updates are classified but **not automatically executed**. They are audited as `vip_update_guarded` to avoid affecting unrelated trades. Full Telegram reply/edit linkage and ticket mapping have NOT been implemented here. This is not a complete automatic signal-update executor.

**Other limitations:** Channel matching is by exact title, not immutable numeric channel ID; verify that only the intended channel uses that title. The 50-pip BE note is advisory only. Real MT5 execution and Windows GUI tests have not been run. Test only on a demo account and confirm that the intended channel is configured as LIMIT.

Validation: Python compilation and 10 unit tests passed. This does not establish live broker correctness.
