# Source validation — EdgeQuant Sentinel v1.9.12 Local Desktop UI V5.1.13 Telegram basic-group sender support

**Build date:** 2026-10-29 (Europe/Bucharest)  
**Python:** 3.13.16  
**Build type:** versioned source preview; no Windows EXE or model checkpoint included.

## V5.1.1 Provider recipients, reports, weekend LIMIT queue and Dashboard controls

- `python -m py_compile edgequant_auto.py edgequant_desktop.py provider_studio.py edgequant_check.py test_provider_studio_v510.py test_sinhala_voice_worker.py` — passed.
- `python edgequant_auto.py --selftest` — **547 passed, 0 failed**. New offline coverage proves fresh-at-receipt LIMIT signals are persisted with exact Telegram IDs and a fixed original-post +72h expiry; the weekend exception is limited to marked LIMIT queue records; initially stale/expired items go to review; price-run and TP-hit guards still reject unsafe reopening prices.
- `python edgequant_desktop.py --selfcheck` — **311 passed, 0 failed**. Includes V5.1 UI/Guide language-role checks and the Receiver Guide's bilingual weekend LIMIT queue instructions, alongside selected recipients, posts/polls, manual-mirror scope/status, Market/Limit views, configurable Layer 1 target, BE option and Excel-check wiring.
- `python -m unittest -v test_provider_studio_v510.py test_sinhala_voice_worker.py` — **10 passed** (5 Provider V5.1 tests and 5 Sinhala voice-text tests). Synthetic offline regressions cover destination + MT5 analytics, report tables/XLSX and linked destination trade counts; logo tests prove embedded Excel media and actionable Pillow-import/invalid-image diagnostics.
- `python edgequant_desktop.py --xlsx-selfcheck` — Provider and Trading Plan XLSX source exports created/reopened successfully with the bundled logo; both ZIP packages contain `xl/media/` image assets. The source-run log is written under the system temporary directory. This does not prove the packaged Windows EXE can load Pillow/openpyxl/`et_xmlfile`.
- `python edgequant_check.py` — exit 0, including the 72h weekend LIMIT queue/build guard; `python edgequant_web_agent.py --selftest` — **13 passed, 0 failed**. Optional Telethon and MetaTrader5 packages are not installed in this sandbox.
- Synthetic Provider and Trading Plan PDF exports succeeded with the bundled logo; both PDFs contain an embedded image marker. `BUILD-EXE.bat` installs and preflights Pillow against the bundled PNG, explicitly collects Pillow and its image plugins, and runs the frozen EXE's `--xlsx-selfcheck`; that self-check embeds the logo in both Provider and Plan workbooks, checks ZIP integrity/`xl/media/`, and reopens all worksheets. Provider's Pillow import error now preserves the underlying exception and gives rebuild guidance. **No Windows/PyInstaller build or frozen-EXE test was run here.**
- Manual mirror remains opt-in, `magic=0` only, excludes EA/algorithm tickets, baselines existing tickets, and does not place/edit MT5 orders. Provider POST/POLL and the weekend queue were validated offline only; no Telegram account/network was connected, no messages/polls were sent, no credentials were accessed, and no MT5 orders were attempted. No new archive was created or uploaded. Existing client-local settings and credentials were not overwritten.

## Historical V5.0.0 Provider automation, manual-order mirror and reports

- `python -m py_compile edgequant_auto.py edgequant_desktop.py provider_studio.py edgequant_check.py` — passed.
- `python edgequant_auto.py --selftest` — **540 passed, 0 failed**. New offline checks cover Market/Limit/current-price MT5 metadata, origin-order IDs for pending-to-open matching, and reconciliation of an older manual trade closed while the app was offline.
- `python edgequant_desktop.py --selfcheck` — **306 passed, 0 failed**. Added checks for linked journal pending/open/TP states, `magic=0`-only mirror captions, Market/Limit labels, Entry/SL/TP/current fields, PRIVATE/PUBLIC username behavior, pips-won/lost aggregation, EOD inclusion of previously opened trades, UI favorites/report integration, separate manual-order type filters, and the V5.0.0 EXE guard.
- `python test_parser.py` — **41/41 passed**; `python test_mt5_external.py` — **4/4 passed**; `python edgequant_check.py` — exit 0. Independent Provider-performance smoke export verified actual **+20/-20** and estimated **+100/-100** pips in Excel/PDF.
- Verified manually without credentials or network calls that private-destination username input clears/disables when PRIVATE is selected and becomes editable/suggested for PUBLIC. (UI source/logic check; native Windows rendering was unavailable.) Manual mirror caption line breaks and nonzero-magic rejection were also checked offline.
- Tests used fake/offline MT5 objects. No Telegram sends, MT5 order placement/modification, account switching, credential access, or archive upload occurred. Windows GUI/PyInstaller/live broker behavior remains unverified. Existing client-local settings/credentials were not overwritten.

## Historical post-V4.9.0 universal broker symbol selection + signal intake

- `python -m py_compile edgequant_auto.py edgequant_desktop.py edgequant_check.py` — passed.
- `python edgequant_auto.py --selftest` — **538 passed, 0 failed**, including exact screenshot-format parsing, generic review when either SL or TP is missing across sources, per-account symbol persistence, fake-MT5 XAUUSDc/XAUUSDm selection, fail-closed behavior for an absent exact symbol, and verification that distinct message IDs are not content-deduplicated.
- `python edgequant_desktop.py --selfcheck` — **300 passed, 0 failed**, including the removal of account-add/remove UI, saved-account default behavior, and the BROKERS-tab per-account XAUUSD/AUTO/XAUUSDm/XAUUSDc chooser.
- `python test_parser.py` — **41/41 passed**. `python edgequant_check.py` — exit 0.
- No client `config.json`, channel settings, state, credentials, or live broker account was changed. Tests used fake MT5 APIs; no order, modification, or Telegram send was attempted. Windows source deployment/PyInstaller build remains unverified.

## Historical V4.9.0 Provider Signal Studio + branded reports + DPI adaptation

- `python -m py_compile edgequant_auto.py edgequant_desktop.py provider_studio.py` — passed.
- `python edgequant_auto.py --selftest` — **542 passed, 0 failed**; includes read-only MT5 quote and disconnected-terminal checks.
- `python edgequant_desktop.py --selfcheck` — **298 passed, 0 failed**; includes Provider-only integration, monitor transition/late-start review, revision-isolated post captions, destination ownership merge, current-input plan export/target status, quote-monitor opt-in/no-order guard assertions, and UI tab construction.
- Independent `provider_studio.py` smoke checks: fresh quote `RUNNING`, TP transition, late-start `REVIEW NEEDED`, and all four Provider-performance/Trading-Plan PDF/XLSX exports. A second smoke run verified a custom uploaded logo is embedded in the Provider report and both plan exports. The plan workbook contains `DAY-BY-DAY PLAN` and `DAILY TARGET` sheets and a current target banner.
- `python edgequant_check.py` — exit 0; source/version/package-file/dependency checks passed. `python -m py_compile edgequant_auto.py edgequant_desktop.py provider_studio.py edgequant_check.py` — passed.
- Regression suites: parser **41/41**; read-only MT5/external-history tests **4/4**; optional remote-agent fail-closed tests **7/7**; Sinhala voice-text tests **5/5**.
- The Windows-specific DPI calls are source-tested only. No Windows GUI, native DPI transition, Windows MT5 terminal, DPAPI runtime, or PyInstaller build was available to validate here. No Telegram send and no MT5 order was attempted. No new archive was built/uploaded.

## V4.8.4 channel list + MT5 connection diagnostics (historical baseline)

- `python -m py_compile edgequant_auto.py edgequant_desktop.py edgequant_check.py` — passed.
- `python edgequant_auto.py --selftest` — **538 passed, 0 failed**. Includes a regression test that historical journal rows and stale OFF keys do not reappear as active sources, and that a linked name+ID mapping renders once.
- `python edgequant_desktop.py --selfcheck` — **291 passed, 0 failed**.
- MT5 poll diagnostics were exercised only by source inspection and offline UI/self-checks. MetaTrader5 is not installed in this sandbox; no live terminal connection/order was attempted.
- The current source tree has empty production route defaults (`LIMIT_CHANNELS`, `MARKET_CHANNELS`, `CHANNEL_IDS`). Existing client-local files may retain old history/settings; the source hotfix prevents history/stale switches from appearing as active source controls.
- No replacement ZIP was built or uploaded. Windows/PyInstaller behavior remains unverified.

## V4.8.3 client-owned API setup checks (historical baseline)

- `python -m py_compile edgequant_auto.py edgequant_desktop.py` — passed.
- `python edgequant_auto.py --selftest` — **536 passed, 0 failed**, including client API ID/hash format checks; the self-test makes no Telegram request or MT5 order.
- `python edgequant_desktop.py --selfcheck` — **289 passed, 0 failed**, including bilingual API setup, login/Settings entry points, DPAPI/source-storage checks, and login button gating.
- The app saves each client's pair in a Windows DPAPI-protected file under `%LOCALAPPDATA%\EdgeQuant`; the current-user encryption/decryption call, native Windows UI, and PyInstaller build were **not runtime-tested** in this Linux sandbox. Validate on a Windows test account before distributing an EXE.
- No Telegram credentials were supplied to or requested from the user. No Telegram login/code request, Telegram message, or MT5 order was attempted.

## Historical V4.8.2 checks completed in the sandbox

- `python -m py_compile edgequant_auto.py edgequant_desktop.py edgequant_sinhala_voice_worker.py test_sinhala_voice_worker.py signal_parser.py test_parser.py test_mt5_external.py edgequant_cloud.py edgequant_check.py edgequant_web_agent.py` — passed.
- `python edgequant_desktop.py --selfcheck` — **282 passed, 0 failed**. Includes the optional installer/status UI, truthful report-dispatch feedback, EXE packaging checks, and screen-off helper contents/copy check. No Tk display server is available; native Windows rendering is not verified.
- `python edgequant_auto.py --selftest` — **519 passed, 0 failed**. Includes a new regression test confirming unknown-signal notification cannot raise `IndexError` and hold the Telegram catch-up cursor, as well as female-only Sinhala SAPI selection, dynamic Sinhala no-English/no-static-clip behavior, report-content checks, and trading safety checks.
- `python -m unittest -v test_sinhala_voice_worker.py` — **5 passed**. Tests Sinhala number/time expansion, decimals, currency/acronym expansion, and character-vocabulary filtering without loading a speech model.
- `python test_parser.py` — **41/41 passed**, including `GOLD SELL 4173 4177` entry-range preservation and ignored TP-result captions.
- `python test_mt5_external.py` — **4/4 passed** with fake/offline MT5 data.
- `python edgequant_web_agent.py --selftest` — **10 passed, 0 failed**. Read-only routes, same-origin browser requests, and disabled remote sign-in/pairing verified without external requests.
- `python edgequant_check.py` — source/version/assets checks passed. MetaTrader5 and Telethon are optional and are not installed in this sandbox.
- No live order was opened, modified, replayed, or closed. No Telegram account or MT5 terminal was connected.

## Owner-requested consecutive-loss pause change (source-only; 2026-10-16)

The consecutive-stop-loss time pause was disabled: `MAX_CONSECUTIVE_SL` defaults to 0, the legacy guard hook no longer blocks based on streak or an old saved timer, and the pause fields were removed from the desktop settings editor. `/streak` remains informational. The separate daily monetary loss limit, daily-target stop, and all other order guards were not changed.

After this change, `python -m py_compile edgequant_auto.py edgequant_desktop.py edgequant_check.py` passed; `python edgequant_auto.py --selftest` passed **521/521** (including the two-SL no-block regression); `python edgequant_desktop.py --selfcheck` passed **283/283** (including the settings-removal check); and `python edgequant_check.py` passed its source/version/assets checks. This is still a source-only modification; it has not been installed or tested in the user's running Windows app. MetaTrader5 and Telethon are not installed here, and no order was attempted.

## Telegram unknown-signal hotfix

The reported log sequence matched the V4.8 defect: `_UNKNOWN_TODAY` was initialized as a one-item list, while `catch_unknown()` read index 2. That raised `IndexError` after the parser rejected the post and caused catch-up to hold the cursor for retry. V4.8.1 stores `[count, date]` consistently and self-tests that an unknown-message notice returns normally. This fixes the retry crash, **not the parser result**. A post logged as `action=ignore, confidence=low` is not sent to MT5; its exact saved text must be examined before changing parser rules. Catch-up messages older than 20 minutes remain deliberately skipped. No replay or MT5 order attempt was made for the reported incident.

## Offline Sinhala voice integration status

The helper, installer, engine/UI routing, text normalization, and unknown-signal catch-up hotfix are present in this V4.8.2 source preview. The ~1 GB VITS checkpoint was **not downloaded**, no TTS runtime was installed, and no model inference or audio playback was attempted here. The offline unit tests do not establish TTS/model compatibility, speech intelligibility, or correct pronunciation.

## Not verified

- Windows rendering, the Windows/PyInstaller EXE build, installer execution, Python 3.11/TTS/PyTorch package resolution, checkpoint loading, CPU/RAM use, or performance.
- Windows SAPI/model audio playback, pronunciation, report-length synthesis, or audio behavior when the display is off.
- Live MetaTrader terminals/accounts, broker history, Telegram login/channel permissions/reconnection/catch-up, or live trading.
- Hosted Supabase setup or remote authentication/sync. Remote access remains disabled; the local web monitor remains read-only.

The optional installer downloads public model/runtime files only after explicit user consent. Report text remains in the local file queue and is not sent to cloud TTS. The V4.7 ZIP and its recorded checksum are unchanged. The V4.8.2 source ZIP includes `SCREEN-OFF-KEEP-LAPTOP-ON.bat`; the helper changes only plugged-in display/sleep timeouts, but actual Windows power-plan behavior was not tested here. It excludes `config.json`, runtime state, logs, Telegram sessions, MT5 account data, installed environments, and the model checkpoint. Review `SETUP.md` and `SINHALA-OFFLINE-VOICE.md` before use; never distribute credentials, sessions, or account data.


## V5.1.1 additions (offline source checks)
- Telegram poll helper tested with a fake Telethon client through the high-level `send_message(file=InputMediaPoll)` route; no live Telegram action occurred. Provider file-upload helper was checked with a temporary test attachment and removed after the fake send.
- New logo and derived compact icon assets are readable; Provider/Plan XLSX self-check embeds the complete brand lockup and verifies `xl/media/`. PDF logo smoke tests remain source-only.
- Sinhala voice source now reports the absent female Sinhala voice/model as a non-speaking condition and directs the user to the local offline installer. Audio playback and Windows SAPI/VITS runtime remain unverified here; the user must install/test a voice on Windows.
- Patch checks: engine **548/548**; desktop **311/311**; Provider/Sinhala tests **10/10**; logo-aware XLSX and two Provider PDF image-embedding smoke tests pass; `edgequant_check.py` exit 0; web-agent **13/13**. No Windows/PyInstaller build, Telegram send, or MT5 order is claimed.

## V5.1.1 report-branding + MT5 native-import build guard (2026-10-25)
- Provider report title is checked end-to-end: Excel workbook metadata and SUMMARY title, PDF cover/page-header brand, and embedded logo. All workbook sheets have an `EdgeQuant Sentinel` bottom-left print footer; PDF keeps the same software credit at bottom-left. Regression `test_provider_report_brand_title_logo_and_edgequant_footer` passed.
- `BUILD-EXE.bat` now checks 64-bit Python and source `MetaTrader5._core` before packaging, collects the native MT5 binaries, then launches a no-terminal-init frozen-app import check. This verifies importability only; it does not prove an installed MT5 terminal can connect to a broker. Windows run/build remains untested here.
- Latest offline results: engine **548 passed**; desktop **313 passed**; Provider/Sinhala tests **11/11**; `edgequant_check.py` exit 0; Python compilation passed; branded Provider PDF/XLSX export test passed. `edgequant_check.py` reports `MetaTrader5` not installed in this Linux sandbox. No Telegram send, MT5 initialize/order, voice playback, settings/credential alteration, or EXE build occurred.
- User decisions still needed before completing related features: message-label vs posting as Telegram channel identity, and the specific safe commands for separate Provider/Receiver-owned bots.

## Telegram Studio destination identity (follow-up, source-only)
- User confirmed the sender should appear as the destination group/channel itself, not as a text label. Signal, plain post, file, poll, manual-mirror and scheduled-report helpers now pass the exact target as Telethon `send_as`. Permission errors do not fall back to the signed-in account and flow to the existing per-destination failure handling.
- Engine fake-client self-test verifies identity arguments for signal/plain/file/poll calls; engine result: **549 passed, 0 failed**. Telethon `>=1.41,<2` is required. No live Telegram send or permission test occurred. Actual success remains dependent on Telegram granting the account the appropriate Send As/admin right for each destination.

## V5.1.2 Telegram Send As permission fix (source-only)
- Reproduced the screenshot's failure condition with a fake `SendAsPeerInvalidError` raised by the media-send path. Before sends, the code queries `channels.getSendAs` for each destination, unwraps Telegram's `SendAsPeer` entries, and only dispatches if the destination itself is listed. No fallback identity is used.
- Offline regressions verify allowed identity dispatch, denied identity stops before any send, and the exact RPC error is translated to guidance. Engine self-test **552/552**; desktop **313/313**; Provider/Sinhala tests **11/11**; source checker and Python compile pass.
- Telegram's account permissions are external: the account must see the target group/channel in that chat's Send As picker. No live Telegram send was attempted; success in the user's chat remains unverified until its owner/admin permissions are set.

## V5.1.3 Provider destination reports + daily EOD PDF/Excel
- Manual OWNED destination report exports filter exact destination IDs in Excel/PDF, use that chat name as report title, embed Provider's configured logo, and retain the EdgeQuant Sentinel footer. The original global Provider-name export remains.
- EOD runs only after the new explicit PDF/Excel opt-in, only in Provider role, and only for successful destination/message-ID pairs published on the current local day. It creates one destination-branded full PDF plus a daily-only Excel workbook per target and sends both with the target's Send As identity. PDF is sent first; partial bundles are recorded for review with no resend. Default time for this new schedule mode is 23:58 local; previous text schedule consent is not reused.
- Offline validation after this change: engine self-test **552 passed**; desktop self-check **315 passed**; Provider/Sinhala tests **13/13**; XLSX packaging self-check reopened Provider + Plan workbooks with logos; `edgequant_check.py` exit **0**; Python compilation passed. The source checker reports MT5 and Telethon absent in this Linux environment as optional runtime dependencies.
- No scheduler tick/live send, MT5 order, credential access, archive upload, or Windows build ran during development. Existing no-retry/idempotent review behavior remains. End-to-end Telegram permissions and Windows time-zone/rendering remain unverified.


## V5.1.4 Signal header, current Telethon Poll constructor, linked journal
- Signal Composer creates a per-recipient header containing that exact group/channel name; Send As remains separate and is still checked.
- `Poll(hash=0)` is included only if the installed generated TL `Poll` signature requires it. Offline fake tests cover hash-required and legacy/no-hash constructors; no poll was sent.
- Provider PDF adds signal-linked journal rows. Excel adds signal ID and symbol/direction to `LINKED MT5 TRADES`; exact destination filtering still restricts the rows. Reports disclose when there are no linked journal trades.
- Verified in this sandbox with offline tests/self-checks only; no Telegram network send, MT5 order, Windows build or settings/credential access.
- Final V5.1.4 offline results: engine **552 passed**; desktop **316 passed**; Provider/Sinhala tests **15/15**; Provider/Plan/daily-EOD XLSX logo self-check passed; source checker exit **0**; Python compilation passed. Telethon Poll construction also verified against 1.41.2 (no `hash`) and 1.45.0 (`hash=0`).

## V5.1.5 Provider journal isolation + explicit MT5 linking + Provider-only Layer 1 (2026-10-25)
- Destination-specific signal first line now replaces the brand: `📊 {destination name} • TRADE SIGNAL`. Per-destination Telegram Send As authorization checks remain independent of that text.
- Provider publications remain in `edgequant_studio_signals.json`; explicit `magic=0` Provider ticket links are stored separately in `edgequant_provider_journal.json`. The Signal Receiver journal is not used as the Provider's publication journal. The Provider Reports page displays per-destination signals with Entry/SL/TP, current manual/automatic progress, linked ticket counts and actual net where confirmed.
- Linking is an explicit selection from the read-only MT5 external snapshot; only `magic=0` is eligible, no automatic/fuzzy matching is used, and no MT5 order or ticket is modified. Linked manual-ticket details flow into Provider PDF/Excel and are filtered to signals published to the selected destination. Unlinked Receiver trades are not included in Provider exports.
- Provider Layer 1 quick TP is separately configurable and passed only to Provider `PUBLISH + PROCESS`; Layer 2 preserves the signal TP. This override does not mutate the Receiver/global Layer 1 setting. `PUBLISH ONLY` posts and journals without MT5 processing; existing TEST/LIVE confirmation and account/channel/broker/freshness/risk gates remain.
- Validation: engine self-test **552/552**; desktop self-check **319/319**; Provider/Sinhala focused tests **17/17**; XLSX self-check passed; `edgequant_check.py` exit **0**; Python compile passed. An optional aggregate test invocation could not import `test_edgequant_remote_agent.py` because the sandbox lacks `cryptography`; the other focused test modules passed. MT5/Telethon packages are unavailable in this Linux environment.
- No Telegram send, MT5 order, credentials/settings access, or Windows build was performed. The user approved V5.1.5 upload; the 59-file, 4,857,371-byte source ZIP was uploaded as TempFile ID `WbwtDLRr3AH` and downloaded back byte-for-byte. Local/remote SHA-256: `7bc129aeaa1e036a6cf1755a49e5e7d3bd31f87e207ffb69b38b0f8ffa53fdf9`. Direct URL: `https://tempfile.org/WbwtDLRr3AH/download`. Expiry: 2026-10-27 23:27:51.598 Bucharest time. TempFile security-scan status was not checked.

## V5.1.5 no-activation Windows client build kit (2026-10-27)
- Frozen-mode settings now save to `edgequant_user_settings.json`; engine startup applies overrides from this editable file, including integer-key restoration for channel-ID maps. Settings reload is source-free in the frozen app. Regression coverage exercises settings persistence and an offline frozen-app smoke test.
- Added `BUILD-CLIENT-INSTALLER.bat`, `SCRUB-CLIENT-DIST.ps1`, and `EdgeQuantSentinel-Client.iss`. The wrapper builds the existing PyInstaller onedir package, scrubs all `.py`/`.pyw` files and local settings/session/log/account data from disposable `dist`, performs MT5 native-module import-only and Provider/Plan XLSX checks, then invokes Inno Setup 6 for a per-user installer. The Inno script independently excludes `.py`/`.pyw`. No license/activation step is added. The optional offline female Sinhala VITS worker/model installer is excluded; compiled Python remains reverse-engineerable.
- Validation in this Linux workspace: Python compile passed; engine self-test **552/552**; desktop self-check **319/319**; Provider/Sinhala unit tests **19/19**; parser **41/41**; external MT5 offline tests **4/4**; XLSX source self-check passed; `edgequant_check.py` exit **0**. No Telegram action, MT5 initialize/order, credentials access, or settings modification occurred.
- This is a developer Windows build kit, not a client installer. Wine/Inno Setup are unavailable here, so the batch, PowerShell and Inno scripts remain unexecuted on Windows. `dist\\EdgeQuant-Sentinel-Client-Setup.exe` has **not** been generated. Follow `CLIENT-SETUP-README.md`; only distribute after the wrapper succeeds and a clean Windows 10/11 x64 PC without Python passes install, first-run, settings persistence and non-live tests.

## V5.1.6 mandatory Telegram auto-reconnect (2026-10-28)
- Startup with an existing session retries transient connection/server errors indefinitely using a 5-second linear backoff capped at 120 seconds. A timeout while the client is still connected (often a phone/code prompt) is surfaced for user action instead of endlessly retrying. Missing sessions and invalid/revoked authorization are not treated as transport outages.
- Active listener disconnects now always retry; the optional/off condition was removed. UI status is marked reconnecting and the stop wait is interruptible. On success, the existing selected-channel recovery loop resumes history catch-up. Message-ID idempotency, freshness, source, TP-hit, account, broker, LIVE and risk checks remain in force; no uncertain broker submission is replayed. Weekend LIMIT queue policy remains limited to its existing 72-hour case.
- Added four fake-client offline tests and made the Windows client builder run them before packaging. No network, Telegram account, session, MT5 initialize/order, credentials or user settings were accessed.
- Validation: Python compile passed; engine self-test **554/554**; desktop self-check **320/320**; focused Telegram reconnect + Provider/Sinhala tests **23/23**; parser **41/41**; external MT5 tests **4/4**; XLSX self-check passed; `edgequant_check.py` exit **0**. The Windows wrapper, PyInstaller and Inno Setup build are still untested in this Linux environment; no client Setup.exe exists yet.

## Strategy/signal update (2026-10-28) — source only, not packaged
- Layer 1 fresh-install default is +50 pips. Pending entries use the confirmed directional +10-pip BUY / -10-pip SELL adjustment; signal SL remains unchanged. Layer 2 selects TP3 when available (otherwise the prior fallback) and moves the selected TP 10 pips toward the adjusted entry. MARKET fills remain at broker quote and apply only the target adjustment. A two-entry range produces four orders.
- Added optional AUTO BE ON/OFF on the Dashboard. It is OFF by default; the trigger/ladder default is +50 pips, with a one-time migration for the former implicit 25/70-pip defaults. Channel BE hints do not override the user setting.
- Same-ID corrected Telegram edits may proceed only after the prior durable journal and latest audit both prove review-only/no order intent. Any placement intent, blocked/uncertain result, or missing record denies the edit. The handler reuses all ordinary freshness, channel, account, risk, broker, LIVE and other safety gates. Duplicate IDs remain one-shot; distinct posts are not content-deduplicated.
- Added offline caption/text parser regressions for the transcribed GOLD/XAUUSD examples and tests for range layering, SL preservation, TP3 choice, +10-pip arithmetic, BE defaults, and the safe review-only edit gate.
- Validation in the original source workspace: engine self-test **553/553**; desktop self-check **320/320**; `python -m unittest discover -v` **38/38**; `edgequant_check.py` exit **0**; `python -m py_compile *.py` passed. The privacy-scrubbed build-kit copy was also checked: engine **553/553**, desktop **320/320**, its included tests **31/31**, source checker exit **0**, compile passed. MT5 and Telethon are absent here, so native import and live listener integration remain for the Windows import log.
- Created a V5.1.7 strategy source/build-kit ZIP. The archive copy omits config/state/session/log files and scrubs the local notification destination, ignore IDs and embedded publishable test key; the original local settings/source remain untouched. No Telegram send, MT5 initialize/order, credential/settings access, or live trade was performed.
- **No Windows client EXE has been built or verified.** The Windows MT5 import-only log and clean Windows 10/11 x64 non-live install/settings checks are still required before distribution.

## V5.1.8 Telegram Studio peer-resolution fix (2026-10-28)
- Fixed destination lookup to prioritize the exact marked Telegram peer ID. Since Telegram peer-type ID spaces overlap, legacy/raw identifiers are accepted only when they resolve to exactly one dialog; ambiguity now fails closed and tells the user to refresh/reselect. The Send As check is unchanged and still refuses to send without destination identity authorization; no personal-account fallback.
- Added an offline regression test with a same-raw-ID basic group and channel, with the wrong-type group listed first. The exact selected channel must resolve, while the ambiguous raw ID must be rejected.
- Validation: engine self-test **554/554**; desktop headless self-check **320/320**; full unit suite **38/38**; `edgequant_check.py` exit **0**; `python -m py_compile *.py` passed. Windows native MetaTrader5 import-only verification and clean Windows 10/11 x64 non-live install testing remain with the user.
- No Telegram send, MT5 initialize/order, credentials access, user-settings access, or live action was performed. This is a source/build-kit update only; no EXE is included.

## V5.1.9 exact-entry management follow-ups + 49-pip Layer 1 (2026-10-29)

- Implemented exact-entry Telegram follow-up handling in `edgequant_auto.py`. The persisted order journal now includes the originating chat ID. A management update may target only a unique original signal ID matching the exact chat/source/category, explicit symbol, BUY/SELL side and exact original signal entry. Both layers at that single entry are grouped; the broker/account and exact ticket list are passed into each modification/cancel/close function. Older records without a chat ID/ticket linkage, no open match, multiple original signal IDs, missing explicit match fields, conditional/advisory instructions, or unavailable MT5 fail closed to manual review/no action.
- BE updates require the owner's AUTO BE switch to be ON and a positive owner trigger; channel instructions cannot enable or replace the owner settings. Complete new signals with an advisory BE note remain on the ordinary signal path. Distinct Telegram posts remain distinct; same chat/message-ID replay is idempotently blocked.
- Layer 1 default changed to +49 pips; Layer 2 retains the selected signal TP and its 10-pip inward shift. Existing BUY +10 / SELL -10 entry offsets and exact signal SL preservation remain unchanged. Historical V5.1.7 documentation still records the prior +50 behavior.
- `python -m py_compile *.py` — passed. `python edgequant_auto.py --selftest` — **556 passed, 0 failed**. `python edgequant_desktop.py --selfcheck` — **321 passed, 0 failed**. Offline unit suite (Telegram reconnect, signal format, new exact-entry follow-up tests, parser, Provider, MT5 external data, remote-agent protocol, Sinhala worker) — **47 passed**. `python edgequant_check.py` — exit **0**.
- The Windows packaged MT5 `_core` import-only self-check and clean Windows 10/11 x64 non-live install test are still mandatory and have not passed. The prior V5.1.8 packaged import check was cancelled after hanging; no log was generated and its cause is unknown. No V5.1.9 Windows EXE or installer is claimed. Do not distribute until build checks and clean-PC tests pass.
- All new testing was offline. No Telegram sends, MT5 initialize/orders, credentials, live trades, or client-local settings were accessed or changed.

## V5.1.10 owner-confirmed reversed entry offsets + opposite hedge-block removal (2026-10-29)

- Entry offsets are now BUY -10 pips and SELL +10 pips across all channels. The screenshot examples are covered: BUY 4039 -> 4038, SELL 4042 -> 4043. The original signal SL remains unchanged; the existing SL validation fails closed if an offset would put it on the invalid side.
- Removed the opposite-direction hedge blocker as explicitly requested. Existing BUY positions no longer alone prevent a valid SELL signal and vice versa. The obsolete setting is no longer editable and old saved values cannot reactivate the guard. Other signal validity/freshness, SL/TP, channel/account/broker, market/news/spread/cap, LIVE and risk checks remain.
- V5.1.9 Layer 1 +49-pip target and exact-entry follow-up behavior remain. Follow-up matching, ticket scope, same-ID replay protection and owner-controlled BE settings are unchanged.
- `python -m py_compile *.py` — passed. `python edgequant_auto.py --selftest` — **556 passed, 0 failed**. `python edgequant_desktop.py --selfcheck` — **322 passed, 0 failed**. Full offline unit suite — **48 passed** after installing the sandbox test dependency `cryptography`. `python edgequant_check.py` — exit **0**.
- The provided log's opposite SELL was skipped by the hedge block; the greetings were correctly non-signals. The hedge block is removed. Malformed, stale, invalid-SL/TP or other risk-blocked messages still must not be force-submitted.
- This remains source-only and offline. No Telegram sends or MT5 orders/initialize were performed. V5.1.8's prior packaged MT5 `_core` check hung and produced no log; its cause remains unknown. The V5.1.10 Windows build, native import-only check and clean Windows 10/11 x64 non-live install are unverified. No client Setup.exe is available to distribute.

## V5.1.11 exact Telegram Chat/Group suffix for explicit channel price-distance rule

- `channel_signal_late_pips` now applies the explicit `CHANNEL_MAX_SIGNAL_LATE_PIPS` owner rule before a saved `late_pips` value, and recognizes only the exact source title or that title plus exact `Chat`/`Group` suffix. Similar/extended names do not match. This fixes the title variant shown in the user's screenshot without broad fuzzy channel matching.
- The special rule only disables the price-run distance guard for the explicitly configured source. It does not bypass freshness/age, TP-hit, exact message-ID, channel ON/OFF, SL/TP validation, account/broker, market/news/spread/caps, LIVE or monetary-risk guards.
- BUY -10 / SELL +10 pips remains mandatory, the original signal SL stays unchanged, and the opposite-direction hedge block remains removed. No active MT5 order is altered by source code changes.
- Main source: `python -m py_compile *.py` passed; engine self-test **556 passed**; desktop self-check **322 passed**; offline unit suite **49 passed**; `edgequant_check.py` exit **0**.
- Sanitized kit: engine **556 passed**; desktop **322 passed**; offline unit suite **49 passed**; `edgequant_check.py` exit **0**; ZIP integrity and private-name/local-state scrub checks passed.
- Uploaded source/build kit: `https://tempfile.org/kPpbmEKHVe4/download`, SHA-256 `fc6fe796702ee0802c6ceee9e88b18a8f9b97a72ad327ae6db6bac6165b3e934`; upload security scan reported safe/no warnings; downloaded ZIP hash matched. Link expires 2026-10-29 04:34 EET.
- Windows native import-only and clean Windows 10/11 x64 non-live installation remain unverified; no Setup.exe is claimed.
- User screenshots showed three relevant states: exact BUY 4055 order was placed by the running app without the requested offset; `TEST LIMIT CHANNEL Chat` was OFF; and a recovered signal was blocked by the global late-distance limit despite the intended channel-specific exception. A code update alone cannot change the already-running Windows app or local channel switch state.

## V5.1.13 — private basic-group Send As peer-type handling

- Owner selected the signed-in Telegram account as sender for a private basic group. `_telegram_studio_is_basic_group` identifies only Telethon `Chat`/`InputPeerChat`; for that peer the app does not call `channels.getSendAs` and does not pass a `send_as` override. Channel/supergroup paths still require exact authorized destination identity and fail closed without fallback.
- Offline regression verifies a basic private group sends via the explicitly selected account path and never requests Send As.
- Main source: `python -m py_compile *.py` passed; engine self-test **555 passed**; desktop self-check **322 passed**; offline unit suite **51 passed**; `edgequant_check.py` exit **0**.
- Sanitized-kit validation and upload follow. Windows native import-only and clean Windows 10/11 x64 no-Python installation remain unverified; no Setup.exe is claimed.

## V5.1.12 — owner-directed removal of the late price-run skip

- Removed the `run > late_pips` rejection branch from `stale_signal`. Any successfully parsed trade-format signal is no longer skipped solely for exceeding the global 40-pip run distance. An offline regression transcribed from the screenshot covers SELL 4033 with market 4026.50 (66 pips past entry).
- `action=ignore / not a signal` logs remain parser non-signals, not skipped order intents. Signal age/freshness and TP-hit guards remain in `stale_signal`; exact message-ID, channel switch, account/broker, market/news/spread/cap, LIVE and monetary-risk gates remain elsewhere.
- Legacy `late_pips` values are retained in old settings for compatibility but are ignored for order rejection; the local command no longer changes that setting.
- Main source: `python -m py_compile *.py` passed; engine self-test **555 passed**; desktop self-check **322 passed**; offline unit suite **50 passed**; `edgequant_check.py` exit **0**.
- Sanitized kit: engine **555 passed**; desktop **322 passed**; offline unit suite **50 passed**; `edgequant_check.py` exit **0**. ZIP integrity/private-name/local-state scrub checks passed.
- Uploaded source/build kit: `https://tempfile.org/9mtaT9SHj9q/download`, SHA-256 `5dc99836fbb0f265b08d348ffcbe251e2eda728d4cea727c745640f462aa1954`; security scan reported safe/no warnings and downloaded hash matched. Link expires 2026-10-29 11:24 EET.
- Windows native import-only and clean Windows 10/11 x64 non-live installation remain unverified; no Setup.exe is claimed.
