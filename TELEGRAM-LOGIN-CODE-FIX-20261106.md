# EdgeQuant — Telegram login SendCodeUnavailableError handling (2026-11-06)

## Fix summary
- **No duplicate resend:** A second SEND CODE click for the same phone returns the existing pending request state. Telethon's `send_code_request` can resend if called again while code is pending.
- **Existing session first:** if Telegram says the saved session is still authorized, login finishes without requesting another code.
- **No cross-phone confusion:** changing the phone during a pending OTP does not dispatch another request.
- **Telegram delivery exhausted:** catches SendCodeUnavailableError, avoids automatic retries, gives actionable guidance, and applies a best-effort local 15-minute pause stored in `edgequant_telegram_code_retry.json` (no number/code saved in that file).
- **One active login client:** expired pending requests reset the old client instead of invoking Telethon's implicit resend on it.
- **GUI:** SEND CODE becomes unavailable while a code is pending; pending state is displayed on reopening the dialog; the 2FA password entry is masked.
- **2FA:** only proceed to 2FA FINISH when Telegram explicitly requires a password.

## IMPORTANT: Telegram server controls login codes
This patch **does not** remove Telegram's limits, deliver a code when Telegram has no delivery method, or bypass Telegram verification. A local pause of 15 minutes does not guarantee Telegram allows requests after that interval. Existing good `.session` files are valuable. Do not delete sessions or repeatedly spam SEND CODE.

## Installing
1. Stop EdgeQuant / any other program using that Telegram session. Back up the *working* project folder, including its `.session` and user settings files. Do not share the `.session` file or the Telegram code / 2FA password.
2. Extract the package to a new folder. Keep your working session/settings data locally and restore them to the same EdgeQuant installation as needed. Never copy the same Telegram `.session` to another running machine.
3. Run `EDGEQUANT-APP.bat` for Python source installs, or `BUILD-EXE.bat` to rebuild an EXE. Existing EXEs do **not** automatically update when Python sources are replaced.
4. In TELEGRAM LOGIN, enter phone in international format. Click SEND CODE **once**, check Telegram's verified service messages, then USE THE CODE; if required, 2FA FINISH.
5. Test in demo before enabling live trading.

## Tests
- `RUN-TELEGRAM-LOGIN-TESTS.bat`: 8 offline mocked Telegram login tests, zero real code sends.
- `python edgequant_auto.py --selftest` on this source: 511 passed / 45 failed, exactly the same result as the unmodified 2026-11-06 source, owing to pre-existing legacy trading-rule test expectations. Do not interpret these 45 as login regressions, or claim full regression suite success.
- **Live Telegram and MT5 validation was not performed.**

## Troubleshooting
- `SendCodeUnavailableError`: stop requesting. Check the official Telegram app for code delivery. Try again only when Telegram permits. Official clients may support other authentication methods that third-party clients cannot.
- `FloodWaitError`: wait the server-specified time. EdgeQuant uses a local backoff but does not override Telegram's restrictions.
- Session already authorized: prefer reusing the same Windows user's session file; do not start concurrent EdgeQuant instances sharing it.
- Codes and passwords should never be pasted into chat or shared with other people.
