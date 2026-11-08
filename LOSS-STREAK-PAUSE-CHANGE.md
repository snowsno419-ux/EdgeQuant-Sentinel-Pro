# Loss-streak pause change — source only

## What changed

- The automatic pause triggered only by consecutive SL results is disabled. Two SL results alone no longer stop new entries for a timed pause.
- Streak counting remains for information in `/streak` and reports; it does not block entries.
- Old saved `streak_pause_until` values are ignored by the updated source.
- The two pause settings are no longer editable in the desktop settings UI.
- The separate daily monetary loss limit, daily-target stop, signal age/duplicate/TP-hit/LIVE checks, and other safeguards are unchanged.

## Applying it

This updates source files in the workspace; it does not change a bot already running on Windows. Stop the bot and back up the existing project before copying the updated `edgequant_auto.py`, `edgequant_desktop.py`, and related check/docs files. If running a Python source build, restart it after replacing the source. If running a Windows EXE, rebuild on Windows with the project's `BUILD-EXE.bat` and test first on a demo account. No command or MT5 order was sent as part of this change.

## Validation

- Engine offline self-test: **521 passed, 0 failed**, including a two-SL case that confirms the streak no longer blocks entries.
- Desktop self-check: **283 passed, 0 failed**, including confirmation the pause settings are no longer editable.
- `edgequant_check.py`: source/version/assets checks passed.
- No Windows runtime, live MT5, or demo-account test was performed here.
