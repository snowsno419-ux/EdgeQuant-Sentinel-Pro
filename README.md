# Current owner update — 2026-11-06

**Direct LIMIT dispatch has superseded the earlier Gold offsets/manual review logic for entry-bearing trade signals. See `DIRECT_LIMIT_OWNER_RULE_20261106.md` for the current behavior, validation limits, tests and deployment instructions. The historical changelog below describes previous versions.**

# EdgeQuant Sentinel v1.9.12 — UI V5.1.13 private basic-group sender compatibility

Telegram-to-MT5 Windows desktop client with local trade execution, plus a **read-only local web console** and selected-channel Telegram history recovery after disconnects. MT5 and Telegram execution remain on Windows. A separate responsive mobile/laptop web control prototype is at `edgequant_web/mobile-control-preview.html`. It now connects to the supplied Supabase project for **email Auth only** (public publishable key); live data, device pairing, command relay and trading remain disabled. The current desktop source also has the consecutive-SL entry pause disabled as requested; the separate daily monetary loss limit and other guards remain. This is a source-only change; this workspace contains no rebuilt Windows EXE.

### 2026-10-29 UI V5.1.13 — private basic-group sender support

- For a Telegram basic private group (`Chat` peer), use the signed-in account explicitly; do not call `channels.getSendAs` or pass an invalid group peer to `send_as`.
- Channels/supergroups still require Telegram authorization for the exact target Send As identity; permission failures stay fail-closed with no fallback.
- This is not the same as a channel/supergroup. A private supergroup still uses the Send As authorization flow; if its peer was misresolved, refresh and reselect the dialog.

### 2026-10-29 UI V5.1.12 — parsed-signal price-run skip removed

- Parsed trade signals are no longer skipped because market price has moved 40/66 or more pips beyond entry. The screenshot's SELL 4033 signal was skipped only by that price-distance rule; this rule is removed.
- BUY -10 / SELL +10 pips remains mandatory; the opposite-direction hedge block remains removed. Signal SL is unchanged.
- Freshness/age, TP-hit, exact message-ID, channel ON/OFF, account/broker, market/news/spread/cap, LIVE and risk checks remain. Lines logged as `action=ignore`, `confidence=low`, `not a signal` are not parsed trade signals; they are not signal-format orders.
- The update is source-only. The current running EXE and existing MT5 orders were not changed. Rebuild and install/test on Windows before expecting runtime behavior.

### 2026-10-29 UI V5.1.11 — exact channel-title alias for the approved late-distance exception

- Exact configured channel name and its exact Telegram `Chat` or `Group` suffix now share that channel's existing price-run distance exception. A saved per-channel distance value cannot silently restore the global price-run block for that explicitly mapped source.
- This changes only the price-distance check for that exact configured source. Signal age, TP-hit, message-ID, enabled-channel, SL/TP, account/broker, market/news/spread/cap, LIVE and risk checks remain.
- The source still uses BUY -10 / SELL +10 pips and has the opposite-direction hedge block removed. Existing open/pending MT5 orders are not changed by this source update.
- The provided screenshots show the running channel was switched OFF, and the old app placed a BUY at the unshifted 4055. Turn the channel ON for new signals and use the updated source build for 4054. No running Windows app or order was modified here.

### 2026-10-29 UI V5.1.10 — reversed 10-pip entry offsets + hedge-block removal

- All channels now use the latest examples: BUY signal entry 4039 → BUY entry 4038; SELL signal entry 4042 → SELL entry 4043 (10 pips each way). Signal SL stays exactly as posted; if a shifted entry makes it invalid, the existing fail-closed SL validation still blocks it.
- Removed the opposite-direction hedge block. An existing BUY alone will no longer stop a valid SELL signal, and vice versa. All other safety gates remain, including signal validity/freshness, SL/TP validation, channel/account/broker, market/news/spread/caps, LIVE and risk limits.
- Layer 1 stays +49 pips; Layer 2 keeps the selected signal TP and its 10-pip move toward the adjusted entry. Two layers per entry remain.
- V5.1.9 exact-entry follow-up protections remain. “Good morning friends” is not a trade signal; the provided log shows that the SELL was blocked by the removed hedge guard, not by the parser.
- No Telegram sends, MT5 initialize/orders, or live actions were used for development. Windows import-only and clean Windows 10/11 x64 install tests remain required.

### 2026-10-29 UI V5.1.9 — entry-scoped Telegram follow-ups + 49-pip quick layer

- Layer 1 quick TP default is now +49 pips per entry. Layer 2 retains the current selected signal target rule (TP3 when available, moved 10 pips toward the adjusted entry). Pending entry offsets remain BUY +10 / SELL -10 pips; the signal SL remains unchanged. Two layers per entry are preserved.
- Clear follow-up management messages may target only a unique, still-open signal entry matching the exact source chat, symbol, BUY/SELL direction, and original signal entry. Both layers for that one entry are grouped. Missing/ambiguous matches, missing durable linkage, broad updates, and conditional/advisory wording go to manual review; no guessing.
- Follow-up BE obeys the owner AUTO BE ON/OFF switch and owner trigger; channel text cannot override the setting. Supported explicit TP/cancel/close instructions are ticket-scoped to the exact matched entry. Distinct Telegram IDs remain distinct; replay of the same chat/message ID is suppressed.
- No Telegram sends, MT5 initialize/orders, or live actions were used for development. Windows import-only and clean Windows 10/11 x64 non-live install tests remain required.

### 2026-10-28 UI V5.1.8 — exact Telegram destination peer resolution

- Fixed Telegram Studio destination lookup: exact marked peer IDs are matched first, preventing overlapping raw IDs from resolving a selected channel to a different basic group. Legacy/raw-ID matches that are ambiguous now stop with a refresh/reselect message.
- The existing Send As authorization check remains fail-closed: the selected destination identity must be returned by Telegram; there is no fallback to the signed-in user. No message is sent when resolution/authorization fails.
- Local regression test covers overlapping channel/basic-group IDs and ambiguous raw-ID rejection. No Telegram send, MT5 connection/order, or live action was used. Windows rebuild and non-live validation are required for this fix.

### 2026-10-28 UI V5.1.7 — Telegram reconnect + clarified signal strategy

- Auto-reconnect remains enforced: a saved Telegram session retries temporary startup/network failures with capped backoff, and the running listener retries after a disconnect. Selected-channel recovery resumes through exact-ID, freshness, source, TP-hit, account, broker, LIVE and risk guards. No uncertain MT5 submission is replayed; only the existing weekend-queued LIMIT exception retains its bounded 72-hour reopening rule.
- Layer 1 defaults to +50 pips. Each entry endpoint receives two orders; a two-entry range therefore plans four. Pending BUY entry shifts up 10 pips, SELL shifts down 10 pips. Layer 2 selects TP3 when available (existing fallback with fewer targets) and moves its selected TP 10 pips toward the adjusted entry. Signal SL is unchanged. Market fills remain at the broker quote and use the same inward target adjustment.
- Added Dashboard AUTO BE ON/OFF; default OFF, with +50-pip trigger default when enabled. Channel BE hints cannot override the user setting. Prior implicit 25/70 defaults migrate to +50.
- Corrected edits of the exact same Telegram ID can be considered only after a durable review-only/no-order-intent result; placed or uncertain IDs remain blocked. Different IDs are never content-deduplicated.
- Offline results: engine **553/553**, desktop **320/320**, unit tests **38/38**, `edgequant_check.py` pass, Python compilation pass. No live Telegram/MT5 action was performed. Windows MT5 import-only and clean Windows 10/11 x64 non-live checks remain pending; this is a build kit, not a ready client EXE.

### 2026-10-25 UI V5.1.5 — Provider journal separation + explicit manual MT5 links

- Signal headers now replace `EDGEQUANT SENTINEL` with the selected group/channel name: `📊 {destination name} • TRADE SIGNAL`.
- Provider signals and Provider trade links are kept in dedicated local Provider journal files, separate from the Signal Receiver journal. The Provider Reports page displays a per-destination signal journal with Entry, SL, TP, progress/outcome, linked-ticket count and actual net where recorded.
- A Provider may explicitly select and link an MT5 `magic=0` manual ticket to a selected Provider signal. There is no fuzzy/automatic ticket matching and no MT5 modification. Provider exports include only trades linked to Provider publications; unrelated Receiver records are not shown.
- Provider `Layer 1 quick TP` pips are configurable separately in the Signal Composer. `Layer 2` remains the exact selected signal TP. The Receiver/global setting is not changed.
- Order processing remains opt-in through **PUBLISH + PROCESS**, with existing TEST/LIVE confirmations and channel/account/broker/risk checks. **PUBLISH ONLY** never processes MT5 orders. No live sends or orders were used for development.

## Run and validate

- Windows desktop: double-click `EDGEQUANT-APP.bat`.
- Local web console: double-click `EDGEQUANT-WEB.bat` (or run `python edgequant_web_agent.py --open`). The agent binds to `127.0.0.1:8765` by default.
- Source: `python edgequant_desktop.py`.
- Offline checks: `python edgequant_auto.py --selftest`, `python -c "import edgequant_desktop; raise SystemExit(edgequant_desktop.selfcheck())"`, `python -m unittest discover -v`, `python edgequant_check.py`, and `python -m py_compile *.py`.
- Windows EXE: run `BUILD-EXE.bat` on a Windows machine. Keep the complete `dist/EdgeQuantSentinel` folder together.



### 2026-10-25 UI V5.1.4 — Provider Signal header, Poll and report-journal fixes

- Each Signal Composer post now appends that specific destination's group/channel name to the `EDGEQUANT SENTINEL • TRADE SIGNAL` header. Multi-destination sends get a different header for each destination; Telegram Send As remains the actual sender identity, and progress/edit updates preserve the destination name.
- Fixed Poll creation for current Telethon TL schemas by supplying `hash=0` only when that installed `Poll` constructor requires it. Kept compatibility with older supported Telethon releases; an offline regression checks both signatures.
- Added a per-signal linked MT5 Trade Journal section to Provider PDFs and linked-signal columns to the Excel trade sheet. Group-filtered reports keep only trades linked to signals published to that destination. When there are no linked MT5 records, the report says so instead of fabricating trades.
- Kept the V5.1.3 per-owned-destination exports and opted-in 23:58 local PDF+Excel schedule. No Telegram send or MT5 order was run during this repair.

### 2026-10-25 UI V5.1.3 — Provider destination reports + daily 23:58 PDF/Excel

- In the Signal Provider workspace, choose an **OWNED** group/channel and export its Trade Journal locally as Excel or PDF. The report is filtered to that destination, titled with its group/channel name, embeds the uploaded Provider logo, and keeps **EdgeQuant Sentinel** in the bottom-left footer. General Provider exports retain the entered Provider brand; Receiver branding remains unchanged.
- Added an opt-in daily Provider PDF + Excel schedule, defaulting to **23:58 local time** for this new report mode. Each destination receives a PDF and workbook containing only successful Provider signals sent there that day, linked MT5 outcomes where recorded, the uploaded logo, destination-name branding, and the EdgeQuant Sentinel footer. Recipients are derived automatically from the day's sent publication records; chats with no successful signal receive no report.
- The new PDF schedule requires its own explicit confirmation; an older concise-text schedule will not silently turn into file sends. Delivery is one attempt per local date/destination (PDF then Excel), failures/uncertain outcomes—including partial bundles—are held for review, and no automatic retry occurs. The app must stay open and Telegram connected.
- No report was sent during development. The Provider-only UI and scheduler are not shown/active in Signal Receiver.

### 2026-10-25 UI V5.1.2 — Telegram destination identity permission fix

- Signal Composer sends the uploaded logo with the signal and requests the selected group/channel itself as the Telegram sender. Before uploading, EdgeQuant checks Telegram’s allowed **Send As** identities for that destination. If the target is not authorized, it stops before sending and explains that the owner/admin must grant the relevant posting/anonymous-admin permission.
- If Telegram still rejects the media send, the per-destination log now translates `SendAsPeerInvalidError` into the same actionable explanation. There is no fallback to the signed-in user; an unapproved sender identity is never substituted.
- Requires Telethon `>=1.41,<2`. This permission check has fake-client regression tests only; it does not test the user's Telegram admin rights or send a live message.
- This update also includes Provider PDF/Excel brand-title and footer changes, and MT5 `_core` EXE-build preflight. Remote Provider/Receiver bot-control commands remain unimplemented, and no Windows EXE was built here.

### 2026-10-25 UI V5.1.1 voice, branding and Provider posting fixes

- The Provider destination directory merges owned/created and all joined groups/channels visible to the signed-in account. It labels OWNED / ADMIN / JOINED access, supports multi-select and has an explicit **ADD SELECTED TO RECIPIENTS** action. The same selected-recipient set is used by the signal composer, posts/polls, and manual-order mirror.
- Added a Provider **POST / POLL** tab. It validates plain-text posts and 2–10 unique poll answers, names the selected recipients in a confirmation, then sends only to those destinations. Failures/ambiguous outcomes are not auto-retried.
- Provider performance now separates live Market positions from pending LIMIT orders; it shows current floating P&L by broker currency and open pips per position, with an explicit read-only/non-realized note. It shows destination-wise publication counts and Market/Limit counts, linked closed MT5 trade counts, wins/losses/BE, TP/SL hits, today's best signal, and separate today TP-hit / SL-hit lists. The tables use local Provider records and MT5 snapshots; they do not place or modify orders.
- Manual MT5 mirroring remains opt-in and strictly `magic=0` only; EA/algorithm tickets are excluded. Existing tickets are baselined. Recipients are captured when mirror is enabled; changing the shared composer selection requires switching the mirror OFF and re-enabling with the new selection. It posts Entry, current market, SL and TP, and continues read-only status updates.
- Dashboard keeps the two-order strategy and exact signal TP on Layer 2, but Layer 1's quick-target distance is now configurable from Dashboard (default +100 pips). Added a separate BE AFTER LAYER 1 ON/OFF control; daily monetary loss-limit and other safety gates are unchanged.
- Signal Receiver: fresh signals on a selected LIMIT source that arrive during explicit weekend market closure are persisted with their original text and exact Telegram chat/message ID. They must pass the normal freshness window on receipt (20 minutes by default); only that queued LIMIT event gets a **72-hour maximum** from the original post. No order is sent while closed. Keep EdgeQuant running with Telegram connected; if offline, it resumes after reconnect only while the item is still within 72 hours. At broker-confirmed reopening, the app re-parses and re-runs source, idempotency, SL/TP, TP-hit/price-run, symbol/account, risk and broker checks before using the normal LIMIT-channel pending-order plan. Expired, changed-source, invalid or uncertain cases go to manual review; interrupted/uncertain submissions are never auto-replayed. Other categories keep their existing freshness policy.
- Added the dedicated **Guide / Upades** tab for Provider and Receiver. Its guidance and section text follows the selected Sinhala/English language, including the weekend queue rules.
- Excel packaging explicitly includes `openpyxl` and `et_xmlfile`; `BUILD-EXE.bat` now invokes a frozen-app CLI smoke test that creates and reopens branded Provider, daily EOD, and Trading Plan workbooks. This sandbox validated source exports, not a native Windows/PyInstaller build.
- Offline validation: engine self-test **547 passed**; desktop self-check **311 passed**; Provider V5.1 synthetic-report tests **3 passed** (8 combined with Sinhala text tests); source Excel/plan export self-check passed; Provider PDF smoke export passed; web-agent self-test **13 passed**; `edgequant_check.py` exit 0; Python compilation passed. Weekend-queue tests cover fresh-on-receipt gating, durable exact-ID storage, 72-hour expiry, and retained price/TP checks. No Telegram send, MT5 order, credential access, or archive upload was performed. Windows GUI/EXE/live-account behavior is not verified.

### Historical 2026-10-25 Provider Studio expansion — UI V5.0.0

- Chat creation suggests an editable public username only for public groups/supergroups and channels. Private destinations use invite links, not public usernames. The composer merges owned and joined destinations, with favorites and a favorites-only view.
- `PUBLISH ONLY` posts without local MT5 processing. `PUBLISH + PROCESS` submits one local engine action for the composed signal (not one per destination); LIVE still requires the typed LIVE gate and preserves freshness, channel/account, broker and risk checks. `LINKED JOURNAL AUTO` tracks the resulting pending/open/closed trades. `MT5 AUTO (READ-ONLY)` remains quote-only and never places/modifies orders.
- Optional manual MT5 mirroring copies only `magic=0` orders/positions to the selected Telegram destinations. It baselines existing orders, shows entry/current market/SL/TP and Market/Limit/Stop type, offers separate order-type views, and updates outcomes from read-only snapshots. EA/algorithm trades are excluded. No mirroring occurs unless explicitly enabled.
- Provider history includes live status, Market/Limit filters, daily/weekly/monthly statistics, actual/estimated pips won and lost, best-signal history, a performance graph, and Excel/PDF exports. Optional local-time EOD Telegram reports are per-destination idempotent and run only while the app is open and Telegram is logged in.
- Offline verification: engine self-test **540/540**, desktop self-check **306/306**, parser **41/41**, external-MT5 tests **4/4**, source check exit 0. Tests used offline/fake MT5 data; no order or Telegram message was sent. Windows GUI/EXE build and live account behavior remain unverified.

### Requested safety adjustment

The consecutive-stop-loss **time pause** has been disabled: a two-SL streak alone no longer blocks new entries. The daily monetary loss limit, daily target stop (if configured), LIVE confirmation, signal-age/duplicate/TP-hit checks, and other guards remain. `/streak` is informational only. The running Windows app will not change until you copy/update this source and restart or rebuild it; no MT5 command was sent.

### 2026-10-22 universal source routing + broker-symbol chooser

- The BROKERS tab no longer exposes an account-add/remove form. It keeps the saved account settings; when an app-saved account exists and no static account is configured, that saved list is used without adding a phantom `MAIN` target. In **BROKERS**, set the exact gold symbol for the saved MT5 account: `AUTO`, `XAUUSD`, `XAUUSDm`, `XAUUSDc`, or a custom exact Market Watch name. The choice is stored separately in `edgequant_broker_symbols.json` and applies to **every signal group routed to that account**. `GOLD` still parses to canonical `XAUUSD`; an explicit choice is exact and fails closed if absent. The screenshot's `XAUUSDc` is an option, not a hardcoded default.
- A placed signal missing **either SL or TP** is sent to manual review for **any user-added signal source** (unless the text explicitly says MARKET/NOW/INSTANT, which retains the existing auto-protection path). Fully protected signals continue through the normal parser, freshness, exact chat/message-ID idempotency, TP-hit, channel/account, LIVE, risk and broker guards. Different Telegram posts are never suppressed just because their content/entry price matches; posts remain separate and old signals are not replayed.
- Exact screenshot regressions cover the TEST LIMIT range/SL/TP/BE note and the detailed two-entry/multi-TP signal. TEST LIMIT CHANNEL remains LIMIT; GOLDEN SNIPER remains MARKET as configured.
- Offline checks: engine self-test **538/538**, desktop self-check **300/300**, parser **41/41**, compilation and `edgequant_check.py` passed. Symbol lookup used fake MT5 APIs only. No live MT5 order or Telegram send was attempted. Existing client account/channel settings were not changed; the running Windows app/EXE needs a source update/rebuild before it uses this feature.


### UI V5.1.1 — Sinhala voice clarity, EdgeQuant brand lockup, poll diagnostics and file posts
- Added the user-provided EdgeQuant logo as the full bundled brand artwork and regenerated the compact UI/window icon and watermark from its mark. Provider default logos, signal posts and notification branding now use the full lockup; user-selected custom logos are preserved.
- Provider text posts can now include one user-selected local file, with an optional caption, explicit destination confirmation, Telegram caption-length validation, and no automatic retry. Poll sends now use Telethon's high-level media-send path, and the exact per-destination failure is written to the local app log instead of only reporting `failed=1`.
- The Sinhala voice panel now says explicitly when no compatible female Sinhala voice is installed and points to the optional local offline voice installer. Dynamic report text stays local; the app does not silently replace Sinhala with English. The model must still be installed and tested on the user's Windows PC.
- Provider PDF cover/page headings and Excel report title/metadata use the entered Provider Brand Name, while the “EdgeQuant Sentinel” credit stays bottom-left in the PDF footer and all workbook print footers. Both include the selected logo.
- The Windows EXE builder checks for 64-bit Python and a working `MetaTrader5._core` import before packaging, explicitly collects MT5 native files, and performs an import-only frozen-app check. It does not connect to a terminal or place orders; this Windows-specific check still needs to be run on the target PC.
- Telegram Studio signals, posts, files, polls, manual-mirror captions and scheduled reports request `send_as` for the destination group/channel itself. Telegram must grant the signed-in account Send As/admin rights; otherwise the send fails with an error and never falls back to the account identity. This requires Telethon `>=1.41,<2`.
- Offline tests exercise poll/file API paths without Telegram access. No Telegram post/poll, MT5 order, or Windows EXE build was sent or tested.

## Web Phase 1 — local monitor

`EDGEQUANT-WEB.bat` starts a responsive browser dashboard and the Windows-side read-only agent. It reads `edgequant_status.json`, `edgequant_trades.jsonl`, and source settings from `edgequant_auto.py`; missing runtime files produce empty states rather than sample/fake trades. The UI refreshes periodically and offers a CSV journal download. The web API exposes no trading or configuration write actions. The server binds to loopback (`127.0.0.1`) by default, so it is for same-PC use only.

## Mobile web migration — Auth + remote source draft

`edgequant_web/mobile-control-preview.html` is the responsive 16-module web UI. Supabase email sign-in is connected, but the relay is not deployed and there is no live data sync. `supabase/migrations/202610150001_edgequant_remote_control.sql`, `supabase/functions/edgequant-relay/index.ts`, and `edgequant_remote_agent.py` are source drafts with offline tests. The Windows agent rejects every command; live remote trading is not ready. See `EDGEQUANT-REMOTE-SETUP-GUIDE.md` before attempting setup. Never port-forward the local agent or put a secret/service-role key in the browser.

## Telegram missed-message recovery patch

A missed Telegram signal during a temporary connection gap was reported; the exact message and cause have not been verified against a live account. The engine now reconciles history for configured sources on startup, after reconnection, and every 30 seconds, using a private per-channel cursor file (`edgequant_telegram_cursors.json`). The first run checks a bounded recent 20-minute window; later scans continue after the saved message ID. It processes recovered messages through the same parser and normal channel, account, LIVE-confirmation, freshness, and risk guards. `ALLOW_OWN_POSTS = False` remains unchanged. The cursor file is included in local auto-backups.

Recovered messages retain their original Telegram timestamp. Signals older than `MAX_SIGNAL_AGE_MIN` (20 minutes) are rejected, and signals whose TP is already reached remain blocked. Per your later channel-specific choice, `TEST LIMIT CHANNEL` has its price-run-distance check disabled; other channels retain the global 40-pip guard. The age, TP, duplicate, channel/account, and risk safeguards still apply. A catch-up message already processed and skipped is not automatically replayed after this setting changes; check MT5 before manually acting on an older signal. Catch-up handling is already integrated in this source package; do not apply a separate patch. See `RELEASE-NOTES-1.9.12.txt` and `SOURCE-VALIDATION.md` for the current changes and checks.

## Fixed trade plan, break-even protection, and 30-minute voice report

- Every signal entry remains locked to **two orders**: Layer 1 uses the Dashboard-configurable quick-target distance (default **+100 pips**); Layer 2 targets the selected signal TP **at its exact price**. The 10-pip pending-entry adjustment does not move the target. `QUICK_TP_PIPS` remains a legacy alias; `LAYER1_TP_PIPS` is the active Dashboard setting.
- If a signal has multiple targets, the existing selection policy remains: TP3 when there are 3 or more targets, TP2 when there are 2, and TP1 when there is 1. If there is no usable signal TP, both layers use the configured Layer 1 quick-target distance.
- BE actions skip losing positions and preserve an SL already at break-even or farther into profit. Ticket/broker-scoped BE changes cannot affect unrelated positions; the adjustable BE ladder remains available.
- The periodic update scheduler checks every 30 seconds against the configured interval (30 minutes by default). Its text report includes realized and floating daily P&L, placed/filled/closed counts, TP/SL/BE/manual results, best closed trade and best channel. The spoken briefing explicitly scopes its figures to EdgeQuant-managed trades and gives the best trade's source and details.
- Sinhala live speech prefers an installed, matching **female Sinhala Windows SAPI voice**; if unavailable, it can use the optional local female VITS model described below. The dynamic report is never reduced to a static clip, and Sinhala never falls back to English. English dynamic speech still requires a matching English Windows voice.
- Voice queue/status logs distinguish “queued/dispatched” from a completed local playback result. The app does not claim speech occurred merely because report text was generated.

## First setup

1. Launch the current desktop with `EDGEQUANT-APP.bat`; each client enters their own Telegram API ID/hash in **LOGIN → API SETUP** (or **Settings → TELEGRAM API SETUP**). The app encrypts them for that Windows user with DPAPI; never ship your personal keys or paste keys/login codes into chat. Older standalone `bot.py` / `telegram_listener.py` launchers are separate legacy paths and do not use this dialog. See `SETUP.md`.
2. Log in to Telegram. EdgeQuant then opens CHANNELS and scans metadata for chats already visible to that account. Select joined groups/channels and add them as LIMIT or MARKET sources.
3. Run TEST RUN before LIVE. START uses an explicit account/risk review and checkbox acknowledgement; it does not ask for the literal word LIVE at startup. Telegram Studio's separate LIVE processing gate remains.
4. The legacy desktop's cloud integration remains deferred: do not enter Supabase keys in its LOCAL PROFILE page or expect its request runner to access cloud services. The separate mobile web prototype has Supabase email sign-in only; it does not sync trading data or send commands. Telegram and MT5 remain local Windows integrations.

## Included changes

- Empty default source lists; explicit multi-select channel onboarding; stopped-bot/singleton protection.
- Telegram Studio public/private creation, username suggestions, invite/contact/join-request controls, multi-destination publishing, optional image logo, and cross-destination signal tracking/edit/delete.
- Updated native desktop UI/UX: the initial role chooser uses a compact brand header, cloud-off badge, hero/callout, large Provider/Receiver cards, and a bottom action bar. The old trading toolbar/menu returns after opening a local workspace. A separate **Web Phase 1** console is included for local, read-only monitoring; it does not replace or disable the desktop.
- Startup role gate: only WELCOME is visible before choosing a role. In this stage, the choice opens a **local Provider or Receiver workspace**—it is not an authenticated cloud role. Provider opens Signal Studio; Receiver opens the local dashboard/source tools. A general local MT5 mode remains available.
- Provider Signal Studio retains validated branded signal composition, 1–10 TP levels, BE advice, single/range entries, logo and Telegram multi-destination publishing. Cloud group publishing is shown as a later-stage placeholder; Receiver cannot see Provider Signal Studio.
- The legacy desktop's Supabase account/group/signal implementation remains a later-stage feature; desktop sign-in and cloud request execution remain blocked. The separate mobile web prototype now has an Auth-only sign-in/create-account flow. It does not connect a shared signal feed, group requests/approval, cloud publishing, cloud reports, live data or trading commands.
- Daily Target and periodic update controls are grouped on the Dashboard, not the generic Settings tab; live progress, sticky daily archive, verified daily-loss unlock, and richer journal/calendar/report P&L + pips + signal levels/timestamps remain.
- Sinhala-safe voice selection and bilingual personalized welcome remain included.
- V4.4 added realized-net channel ranking, Channel Progress outcomes, a today-opened non-EdgeQuant Manual Trades view, external MT5 daily realized P&L, and guarded local-only ticket edits.
- V4.7 (base) extends V4.6: the summary-first Dashboard is preserved and now also includes dedicated Open Trades and Pending Orders tables; the Journal adds broker MT5 history, capital and channel P&L; selected-language voice reads signal and order times/details. The V4.7 archive remains unchanged.
- V4.8 adds an optional offline female Sinhala speech route for dynamic reports and event details. It does not change trading, Telegram, or report-content rules.

### V4.9.0 Provider Signal Studio + branded reports + DPI adaptation

- Provider-only Signal Studio separates destinations created by this Telegram account from groups/channels the account has joined. It adds searchable destinations and locally saved favorites; choose any number of normal/favorite targets for one explicit publish. Telegram can list only chats available to the logged-in account; private groups cannot be discovered by title without account access or a link/ID.
- The publication tracker shows a separate journal of posted signals with full entry/SL/TP, destinations, status and tracking mode. **LOAD TO FORM** pre-fills a selected signal before explicit edits; updating a caption edits the original Telegram posts only and never changes an MT5 order. Broker ticket changes remain a separate, explicit action.
- Optional **MT5 AUTO (READ-ONLY)** polls fresh quotes from an already connected terminal. It never initializes/switches accounts or places/modifies orders. It updates original posts only for a clear status transition; long monitoring gaps, missed entries and ambiguous price ordering go to manual review. Keep this PC and MT5 terminal open; demo accounts are fine. Manual and linked-journal tracking remain available.
- Provider-only day/week/month/all-time cards and exports include signal counts, wins/losses/BE, win rate, TP hits by level, actual linked MT5 pips/net when recorded, nominal signal pips, best signal and tracking details. Upload a provider logo/name for branded editable Excel and premium PDF exports. Trading Plan exports add a day-by-day sheet, formulas, and a prominent current daily-target achievement/status panel in Excel/PDF.
- Windows per-monitor DPI awareness and adaptive Tk scaling improve readability across display resolutions; saved window sizing remains bounded to the current screen. The top card now gives actionable MT5 connection guidance and terminal/account diagnostics.
- Packaging now includes `provider_studio.py`, Pillow and openpyxl. Offline validation: engine self-test **542 passed, 0 failed**; desktop self-check **298 passed, 0 failed**; compilation passed; independent monitor/export smoke tests produced valid PDF/XLSX files. No Telegram send or MT5 order was attempted. Windows rendering, Windows MT5 diagnosis, and PyInstaller build are still unverified; this is source-only and no replacement ZIP has been uploaded.

### V4.8.4 channel sources + MT5 connection diagnostics (historical baseline)

- The packaged routing defaults remain empty. The CHANNELS switch list now shows only currently configured LIMIT/MARKET sources; it no longer turns old journal entries or stale OFF keys into apparent active channels. A source added by name and Telegram ID appears once by its friendly name, and the ON/OFF switch matches either alias; ID-only mappings remain visible. Removed the unrelated hard-coded channel name from the help tip.
- MT5 status polling now retains `MetaTrader5.last_error()` when `initialize()`, `terminal_info()`, or `account_info()` fails, and distinguishes an open terminal with no broker connection/account. The Dashboard shows a concise reason; the BROKERS page shows the full diagnostic. This is read-only status work and does not attempt an order.
- Offline checks: engine self-test **538 passed, 0 failed**; desktop self-check **291 passed, 0 failed**; Python compilation passed. Windows MT5/DPAPI and PyInstaller behavior remain unverified; no live Telegram or MT5 action was performed.

### V4.8.3 client-owned Telegram API setup

- The desktop login dialog now has an **API SETUP** button; the Settings page has **TELEGRAM API SETUP**. Both open the same short English/Sinhala guide with an **OPEN TELEGRAM API PAGE** button, API ID/API hash fields, masked hash input, and **SAVE SECURELY**.
- Each client enters their own `api_id` and `api_hash`; the package contains no seller/client API credentials. The app validates the pair and stores it encrypted with Windows DPAPI for that Windows user under `%LOCALAPPDATA%\EdgeQuant`. The UI does not send a Telegram request while saving; credentials are used with Telegram only after **SEND CODE**.
- `EDGEQUANT_API_ID` / `EDGEQUANT_API_HASH` environment variables remain a compatibility fallback. The saved DPAPI pair takes precedence. Login buttons stay disabled until a valid pair is available.
- No Telegram code, Telegram message, or MT5 order was sent for this UI change. The native Windows DPAPI operation and a Windows/PyInstaller EXE build still require verification on a Windows machine.

### V4.8.2 full package: signal cursor hotfix + screen-off helper

- Includes `SCREEN-OFF-KEEP-LAPTOP-ON.bat`: plugged-in monitor timeout 5 minutes, sleep Never on AC. Battery sleep, hibernation and lid-close behavior are left unchanged. Keep the charger connected and lid open; the script has not been run on Windows in this sandbox.
- Includes the V4.8.1 fix for an `IndexError` in the unknown-signal notice counter. The old one-item list was accessed at index 2, so a parser-rejected Telegram post could make catch-up fail and hold its cursor for retry.
- Enabled sources are processed through the parser and existing guards. Only recognized, fresh entry signals proceed toward the configured MT5 account; a channel being ON does not make chat, TP-result captions, duplicates, stale signals, or unrecognized text an order. The 20-minute freshness limit and other safety checks remain.
- The fix prevents the retry crash; it does **not** make an unrecognized Telegram post actionable. If logs show `action=ignore, confidence=low`, no order is sent. Inspect the exact original post saved in `unknown-signals.txt` before changing parser rules. No replay or MT5 order was attempted for the incident shown in the logs.

### V4.8 Optional offline female Sinhala speech (preview; device test required)

- The VOICE panel includes **INSTALL OFFLINE VOICE**. It asks before opening the Windows installer and uses a separate Python 3.11 environment; it does not replace EdgeQuant's existing Python/runtime.
- The installer obtains the Dialog/UoM `SinhalaVITS-TTS-F1` checkpoint (female speaker Nipunika; about 1 GB) from Hugging Face and PyTorch/TTS packages from PyPI. The checkpoint is not bundled. Allow several GB of free space; CPU inference may be slow, and RAM/performance requirements are not measured. The model card declares MPL-2.0; review its current terms before redistributing it. See `SINHALA-OFFLINE-VOICE.md`.
- After installation, the installer synthesizes and plays a sample before marking the local voice ready. Restart EdgeQuant (or press REFRESH), select `SI`, and use TEST before relying on reports. Runtime synthesis and Windows playback are local; report text, channel names, prices, and P&L are not sent to cloud TTS or the model-download host.
- If the offline worker accepts a report, the UI says it is queued; playback is reported only after the worker writes a success result. If no female Sinhala route is available, dynamic figures are not spoken through a static clip or English fallback.
- **Not verified here:** Windows installer execution, dependency/checkpoint compatibility, model inference, Sinhala pronunciation quality, audio hardware/playback, or performance. V4.8 is an integration preview, not a validated working voice on Windows.

### V4.7 Dashboard orders, MT5 history, and voice detail

- Kept the Dashboard summary cards/KPIs, outcome overview, target, rankings and Channel Progress/Manual Trades views. Added separate **OPEN TRADES** and **PENDING ORDERS** lists beneath the overview.
- Pending MT5 LIMIT orders show the source channel, account, entry, market price, SL/TP, signal received time, order-placed time, age and ticket. Open rows show MARKET positions and triggered LIMIT positions, including live price/floating P&L and active time. A filled LIMIT is removed from pending and appears under Open Trades on the next live poll.
- Live/pending rows are read across configured MT5 accounts without changing trading behavior. Journal remains the detailed historic record and now adds a separate **MT5 HISTORY** page for all history returned by the connected terminal, live balance/equity, realized and floating P&L by currency, and realized P&L for journal-matched signal channels. Unmatched MT5 deals are labeled Manual / Other EA rather than assigned to a guessed channel.
- Signal voice detail includes received time, account, order parameters and ticket; a fill event includes activation time and live order details. The periodic voice summary includes available account balance/equity and realized P&L by channel. Sinhala content stays Sinhala and does not fall back to English; V4.8 adds an optional local female model for live figures.
- V4.7's reported offline validation remains a historical baseline: desktop self-check 280/280; engine self-test 515/515; parser 41/41; fake-MT5 4/4; web-agent 10/10. Current V5.1.1 checks (with V5.1.0 as the previous baseline) and historical V5.0.0/V4.9.0/V4.8.4 details are in `SOURCE-VALIDATION.md`. No live account/Telegram test or native Windows rendering/build is claimed.

- V4.6 supersedes the unsuccessful V4.5 package with a summary-first Dashboard, Journal detail subpages, and the corrected conversational Sinhala briefing described below.

## V4 desktop update

- The native desktop header now fills the former empty right-hand area with a pulsing MT5 account card. It shows account name/login, broker/company/server, balance/equity and a conservative REAL/DEMO/CONTEST status; multiple accounts are listed by identity and mixed currencies are never summed. The Dashboard repeats the account identity.
- Dashboard metric cards now have layered shadows/accent edges for a more dimensional, premium look.
- **CHANNELS → ADD SOURCE / SEARCH JOINED GROUPS** filters already-visible Telegram dialogs by name. Select a joined private group/channel and add it as LIMIT or MARKET; there is no invite-link join flow. The app saves its name + Telegram ID and listens for new messages after START, with the existing STOP + singleton lock required for scanning.
- **TRADE JOURNAL** now renders every loaded JSONL record; there is no per-channel 400-row cutoff. Uncheck “today only” and scroll to view old trades.
- **Dashboard → DAILY LOSS CAP** saves a local USD loss cap (0 = off). **UNLOCK TODAY** remains a confirmed, same-day override and resets automatically the next day.
- Personalized bilingual welcome remains visible at startup and Telegram login; the selected voice language speaks its matching greeting. Daily-target completion forces one selected-language voice alert per day. Sinhala mode never falls back to English audio.
- Daily Target stays in its own Dashboard section; daily-loss protection, compounding, stop-after, voice and periodic updates are explicit controls outside Settings.

### V4.6 Summary-first Dashboard, Journal pages, and Sinhala briefing

- V4.6 supersedes the rejected V4.5 package. The left navigation rail remains, but the desktop redesign now changes the actual workspaces as well: Dashboard is an aggregated overview rather than a renamed tab strip.
- Dashboard shows daily realized P&L, current MT5 floating exposure, EdgeQuant target progress, open/pending totals, daily TP/SL/BE/manual counts, one best-trade spotlight, period summaries, and aggregate source/performance views. It does not show ticket-level tables.
- **TRADE JOURNAL** now has separate **Trade History**, **Open & Pending**, **Best Trades**, and **Profit Flow** subpages. Individual historical/live/pending ticket details stay here; the live/pending tables continue refreshing while Journal is selected. **Channel Progress** and **Manual Trades** remain separate main views.
- Scope is explicit: Dashboard daily realized P&L includes non-EdgeQuant MT5 closes booked today (including positions opened earlier), without double-counting EdgeQuant. The target and spoken report remain EdgeQuant-managed only. Manual Trades includes all non-EdgeQuant MT5 tickets opened today, including other EAs.
- The on-demand/periodic Sinhala briefing is conversational and says it covers EdgeQuant-managed trades only. It covers today's realized and open floating P&L, target amount/progress/status, trade activity, TP/SL/BE/manual outcomes and counts, and the best trade with source channel, symbol, direction, result and pips.
- **Dashboard → READ TODAY'S REPORT** runs the report without sending it to Telegram. A matching installed Windows Sinhala speech voice is required for live figures; otherwise only the static Sinhala clip may play, with no English fallback.
- The role-aware navigation rail, local-only ticket editor, incoming-only Telegram processing, two-order TP behavior, profit-protecting BE, and the opt-in keep-system-awake/allow-display-off behavior remain in place.
- Offline checks after the V4.6 corrections: desktop self-check **274 passed, 0 failed**; engine self-test **510 passed, 0 failed**. Windows rendering/SAPI and live MT5/Telegram behavior remain unverified here.

### V4.4 Local trade center and Channel Progress

- Channel ranking uses realized net P&L, highest first; win rate breaks ties. The separate Channel Progress tab lists channel trades and TP / BE / SL / manual-close outcomes.
- The Manual Trades tab shows non-EdgeQuant MT5 trades opened today, including positions from other EAs. Dashboard daily realized P&L also includes non-EdgeQuant exits booked today—even when the position opened earlier—without counting EdgeQuant-origin tickets twice.
- Ticket edits are available only in the local desktop: pending-entry, TP and SL changes plus profit-protecting break-even require explicit confirmation and validate one selected ticket. No orders are opened or closed by these edit controls. Dashboard remains summarized; detailed records live in their own tabs.
- Offline validation passed: desktop 272/272, engine 508/508, external MT5 tests 3/3, parser 41/41. Live MT5/Telegram behavior, Windows rendering, and EXE packaging still need target-device testing.

### V4.3 Dashboard history and incoming-only signal diagnostics

- BEST TRADES defaults to ALL history; change the period buttons to DAILY/WEEKLY/MONTHLY as needed. Per-trade details remain in TRADE JOURNAL.
- Weekly/monthly metrics show placed, filled, closed and missed counts separately. Weekly top-channel P/L is ranked using closed outcomes only.
- Own outgoing posts remain ignored by default (incoming-only). If your own post is in a tracked group, a clear local log entry explains the ignore; another group member/account must send a message for it to be incoming.

### V4.2 Dashboard power option

A Dashboard **KEEP SYSTEM AWAKE • ALLOW DISPLAY OFF** opt-in prevents Windows system idle sleep while EdgeQuant remains open. It deliberately leaves Windows' display timeout enabled, so the monitor can turn off while MT5 and EdgeQuant continue running. The option defaults OFF, is session-only, and is cleared when the app closes. Set the screen-off timer in Windows Power settings; closing a laptop lid may still trigger the configured lid action.

### V4.1 Windows EXE build patch

The V4.1 package fixes the `BUILD-EXE.bat` source-version guard: it now accepts the full `desktop 1.9.12 UI-V4.1` identifier, instead of rejecting any suffix after `desktop 1.9.12`. Its success banner and extraction instructions match the V4.1 package. The Windows/PyInstaller build still needs to be run on a Windows PC.

## Voice behavior

Sinhala mode uses only Sinhala recordings, a matching female Sinhala Windows SAPI voice, or the optional offline female VITS worker. Dynamic reports are not replaced by a static clip and never fall back to English. If no suitable live-figure voice is ready, the app says so. The full `voice/` folder, `edgequant_sinhala_voice_worker.py`, and `INSTALL-SINHALA-FEMALE-VOICE.bat` must ship beside the EXE.

## Safety / commercial readiness

Telegram session files remain local. Never send a login code, 2FA password, `.session` file, MT5 password, or Supabase secret/service-role key. The legacy desktop uses no cloud API; the separate mobile web preview has Supabase Auth only. The secure relay/migration/agent source is prepared but not deployed; no live data or remote MT5 actions work yet. Offline per-PC lifetime licensing/activation is a stated requirement but is not implemented in this build.

See `SETUP.md` (Sinhala setup guide), `SINHALA-OFFLINE-VOICE.md`, `EDGEQUANT-WEB-PHASE1.md`, `RELEASE-NOTES-WEB-PHASE1.txt`, `RELEASE-NOTES-1.9.12.txt`, and `SOURCE-VALIDATION.md` for setup, web architecture, validation results, and remaining live-service/licensing limitations.
