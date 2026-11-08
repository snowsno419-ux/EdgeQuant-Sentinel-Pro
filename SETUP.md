# EdgeQuant Sentinel 1.9.12 — ස්ථාපන මාර්ගෝපදේශය

> **තත්ත්වය:** v1.9.12 V5.1.13 source update එකකි. Windows EXE rebuild එකක් මෙහි ඇතුළත් නොවේ. Supabase/Cloud සම්බන්ධතාව අක්‍රියයි. Telegram සහ MT5 local integrations භාවිතයට setup අවශ්‍යයි; live Telegram/MT5 හෝ native Windows rendering මෙහි පරීක්ෂා කර නැත.

## v1.9.12 Local Desktop UI V5.1.13 — private basic-group sender

Telegram normal/basic private group ekakata oyage login account eken post karanna; `channels.getSendAs` call karanne na. Channels/supergroups walata selected destination Send As permission thama required; permission fail unoth personal-account fallback ekak naha.

## v1.9.12 Local Desktop UI V5.1.12 — parsed signal price-run skip off

Oya dunna recognized trade format parse wela `action=place` una signal ekak, market eka entry eken pips gananak giya kiyala skip karanne na. Screenshot eke `SELL 4033` skip kala 40-pip condition eka ain kala. Age/freshness, TP-hit saha existing safety checks thama active. `action=ignore / not a signal` log ekak valid trade signal ekak nemei.

## v1.9.12 Local Desktop UI V5.1.11 — Chat/Group title late-check alias fix

Configured channel name ekata exact `Chat`/`Group` suffix ekak append una nam, e channel eke owner-approved late-distance exception eka apply wenawa. Saved per-channel price-distance value eka e explicit exception eka override karanne na. Signal age, TP-hit, channel ON/OFF, SL/TP, account/broker, LIVE saha risk guards thama active.

## v1.9.12 Local Desktop UI V5.1.10 — reversed offsets + hedge guard removed

BUY signal entry 4039 nam BUY entry 4038; SELL signal entry 4042 nam SELL entry 4043 (10 pips). Me offset eka channels okkotama. Original signal SL eka unchanged. Opposite BUY/SELL hedge block eka remove kara; anith freshness, valid SL/TP, channel/account/broker, market/news/spread/cap, LIVE saha risk checks thiyenawa. Layer 1 +49 pips; Layer 2 selected TP ekama 10 pips entry ekata inward. V5.1.9 exact-entry follow-up rules pawathe.

## v1.9.12 Local Desktop UI V5.1.9 — entry-scoped follow-ups + 49-pip Layer 1

Layer 1 quick target default eka +49 pips. Layer 2 current signal TP selection/inward 10-pip adjustment ekama. Earlier offsets BUY +10 / SELL -10 pips hitiya; signal SL unchanged. Follow-up updates only exact same chat + symbol + direction + entry unique match ekakata witharai; ambiguous updates manual review. BE updates owner AUTO BE ON/OFF saha owner trigger yata.

Telegram Studio now resolves the exact marked peer ID first. If an older/raw ID could identify multiple peer types, it fails closed and asks you to refresh/reselect the destination. Send As authorization is still required; the app never falls back to your personal account. Rebuild the client from this updated source before testing this fix.

### Telegram disconnect වුණොත් auto-reconnect

Telegram network drop වුණාම active listener එක capped backoff එකකින් ස්වයංක්‍රීයව reconnect උත්සාහ කරයි. Saved Telegram session එකක් තිබියදී startup network error වුණත් retry කරයි; reconnect වූ පසු තෝරාගත් channels වල history catch-up එක පවතින freshness, exact message-ID, TP-hit, account, broker, LIVE සහ risk gates හරහා යයි. Uncertain MT5 submission එකක් නැවත යවන්නේ නැහැ. Telegram authorization එක revoke/unregister වීම, වැරදි API keys, හෝ මුල් login එකක් network retry එකෙන් විසඳෙන්නේ නැහැ—එවිට app එක user LOGIN ක්‍රියාවක් ඉල්ලයි. Reconnect වීම internet/Telegram සේවාව නැවත ලබාගත හැකිවීම මත රඳා පවතී; Windows build එකේ native test අවශ්‍යයි.

### V5.1.5 Provider journal වෙනස්කම්

Signal පළමු පේළියේ brand එක වෙනුවට තෝරාගත් destination group/channel නම යෙදේ: `📊 {destination name} • TRADE SIGNAL`. Provider signals සහ Provider manual ticket links වෙනම local journal files තුළ සුරැකේ; Signal Receiver journal එකට ඒවා එකතු නොවේ. Provider Reports හි destination අනුව signal, Entry, SL, TP සහ manually marked TP/BE/SL progress පෙන්වයි.

Provider signal එකක් තෝරා MT5 snapshot එකෙන් `magic=0` manual ticket එකක් පැහැදිලිව තෝරා link කළ හැක. Auto/fuzzy matching නැත; MT5 ticket එක modify නොකරයි. Provider PDF/Excel තුළ එම Provider signal එකට link කළ tickets පමණක් පෙන්වයි. Provider Layer 1 quick-TP pips වෙනම configure කළ හැක; Layer 2 signal TP එකමයි. `PUBLISH ONLY` order process නොකරයි; `PUBLISH + PROCESS` පමණක් පවතින TEST/LIVE සහ account/broker/risk gates හරහා process කරයි.

Signal Provider report page එකෙන් OWNED group/channel එකක් තෝරා එම destination එකට පමණක් සීමා වූ Trade Journal PDF/Excel එකක් manual export කළ හැක. Report title එක group/channel නමයි; Provider upload කළ logo එක embed වේ; footer එකේ EdgeQuant Sentinel පවතී. Receiver report වෙනස් කරන්නේ නැහැ.


Signal Composer එකෙන් destinations කිහිපයකට යවන විට සෑම signal message එකකම පළමු line එක `📊 {destination name} • TRADE SIGNAL` ලෙස, එම post එක ලැබෙන group/channel නම brand එක වෙනුවට යෙදේ. Telegram sender identity එක actual Send As destination එකමයි.

Poll issue එකේ `Poll.__init__() missing ... hash` error එක fix කරලා තියෙනවා: install කර ඇති Telethon version එකේ `Poll` constructor එකට අවශ්‍ය නම් පමණක් `hash=0` යොදනවා.

Provider PDF එකේ signal එකකට link වූ MT5 Trade Journal rows පෙන්වයි; Excel `LINKED MT5 TRADES` sheet එකේ Signal ID සහ Signal symbol/direction ද පෙන්වයි. MT5 journal එකේ trades නොමැතිනම් report එක ඒ බව පැහැදිලිව පෙන්වයි—fake trades හදන්නේ නැහැ. V5.1.3 per-destination PDF/Excel සහ opt-in 23:58 schedule එක පවතී.

Daily Provider PDF + Excel schedule එක opt-in වන අතර නව install එකක local time **23:58** ලෙස පෙන්වයි. Enable කළොත් එදින signal සාර්ථකව යැවූ destinations වලට පමණක් ඒ ඒ group/channel name/logo සහිත PDF එක සහ Excel workbook එක යවයි. අලුත් schedule එකට වෙනම confirmation අවශ්‍යයි; app එක විවෘතව සහ Telegram connected තිබිය යුතුයි. Bundle එක partial වුණත් failed/uncertain send එක auto-retry නොවේ. Build/testing අතර report කිසිවක් යවා නැහැ.

Telegram Studio හි signal, user-uploaded logo, poll සහ post යැවීමට පෙර target group/channel එක Telegram හි Send As list එකේ තිබේදැයි පරීක්ෂා කරයි. Target identity අවසර නැත්නම් යැවීම නවතා, Telegram owner/admin වෙතින් අවශ්‍ය posting/anonymous-admin අවසර ලබාදීමට උපදෙස් දෙයි. EdgeQuant ඔබේ personal account නමින් fallback කරන්නේ නැහැ. මේක සඳහා Telethon `>=1.41,<2` අවශ්‍යයි.

> Provider → DESTINATION DIRECTORY හි signed-in Telegram account එකට දැනටමත් පෙනෙන/එක්වී ඇති groups සහ channels සියල්ල refresh කරන්න. OWNED / ADMIN / JOINED තත්ත්වය බලන්න; rows කිහිපයක් තෝරා **ADD SELECTED TO RECIPIENTS** ඔබන්න. Signal Composer, POST / POLL සහ manual mirror එකම recipient selection එක භාවිතා කරයි.
>
> **POST / POLL** තුළ plain-text post එකක් හෝ poll question එකක් සකසා **SEND** කිරීමට පෙර recipient confirmation බලන්න. Post එක selected destinations වෙත පමණක් යවයි; poll එකට අද්විතීය පිළිතුරු 2–10ක් අවශ්‍යයි. අසාර්ථක/අවිනිශ්චිත යැවීම නැවත ස්වයංක්‍රීයව නොයවයි.
>
> Provider Reports හි Market = විවෘත MT5 position; Limit = pending LIMIT order. Floating P&L වෙනස් විය හැක; pips එක් එක් position සඳහා පෙන්වයි. Live view කියවීම පමණි. අද TP-hit / SL-hit ලැයිස්තු signal tracking වේ; broker සැබෑ ප්‍රතිඵල සඳහා linked journal trades අවශ්‍යයි.
>
> **Receiver weekend LIMIT queue:** Broker එක FX weekend market closed බව තහවුරු කරන විට LIMIT source එකකට ලැබෙන fresh signal එක exact original text + Telegram chat/message ID සමඟ local `edgequant_signal_deferred.json` තුළ save වේ. මුලින් ලැබෙන මොහොතේ සාමාන්‍ය freshness limit එක pass විය යුතුයි (default විනාඩි 20); මේ queued LIMIT item එකට පමණක් original post සිට උපරිම පැය 72ක් දක්වා queue window එකක් ඇත. Market closed විට order නොයවයි. EdgeQuant ධාවනයේ සහ Telegram connected තබන්න; offline වුණොත් 72h ඇතුළත reconnect කළ විට පමණක් යළි process වේ. Broker market open බව තහවුරු කළ පසු signal එක නැවත parse කර source ON, duplicate/message ID, SL/TP, TP-hit/price-run, symbol/account, risk සහ broker checks සියල්ල නැවත පරීක්ෂා කරයි. සියල්ල pass වුවහොත් පමණක් LIMIT-channel pending-order plan එක යයි. පැය 72 ඉක්මවූ, source වෙනස්/OFF වූ, invalid, stale-quote හෝ uncertain item manual review වෙත යයි; crash/interrupted submission auto-replay නොකරයි. වෙනත් channel categoryවල freshness වෙනස් කර නැත.
>
> Dashboard → **LAYER 1 QUICK TARGET (pips)** සකසා APPLY කරන්න (default +100). Layers දෙකම පවතී; Layer 2 exact signal TP භාවිතා කරයි. **BE AFTER LAYER 1** ON/OFF වෙනම පාලනයකි. Daily monetary loss limit සහ වෙනත් safety checks වෙනස් කර නැත.
>
> **Guide / Upades** tab එක Provider/Receiver role-වලට ගැළපෙන උපදෙස් පෙන්වයි; language selector එක Sinhala/English අනුව guidance මාරු කරයි.

## Historical v1.9.12 Local Desktop UI V5.0.0 — Provider automation + manual-order mirror

> Public group/supergroup/channel create කිරීමේදී name එකෙන් editable `@username` suggestion එකක් ලැබේ. ඒක Telegram availability තහවුරු කිරීමක් නොවේ. **Private destination** එකකට public username භාවිතා නොවේ; invite link එක භාවිතා කරන්න. Composer එක owned සහ joined destinations එකට පෙන්වයි; favorites සහ **FAVORITES ONLY** view එක ඇත.
>
> **PUBLISH ONLY** = Telegram destinations වලට පළ කිරීම පමණයි. **PUBLISH + PROCESS** = signal එක running local engine එකට එක් වරක් යොමු කරයි. LIVE engine එකේ typed `LIVE` gate එක අනිවාර්යයි; TEST RUN සැබෑ order නොයවයි. Linked Journal Auto actual pending/open/closed outcomes පසුපස යයි. **MT5 AUTO (READ-ONLY)** quote tracking පමණයි—orders place/modify නොකරයි.
>
> Optional **manual MT5 mirror** එක enable කළ විට පමණක් magic=0 manual positions/pending orders තෝරාගත් Telegram destinations වලට copy කරයි. EA/algorithm orders පිටවෙයි. Existing tickets baseline කර skip කරයි. Entry, current market, SL/TP සහ Market/Limit/Stop type පෙන්වා close/outcome එක read-only MT5 snapshots මගින් update කරයි.
>
> Provider reports තුළ daily/weekly/monthly stats, wins/losses/BE, actual/estimated pips won/lost, best signal, history, graph සහ Excel/PDF export ඇත. Local-time scheduled EOD reports opt-in වේ; app එක open සහ Telegram login active තිබිය යුතුයි. No live order/message was sent while building this source.

## Historical v1.9.12 Local Desktop UI V4.9.0 — Provider Studio, exports + DPI fit

> **V4.9.0 Provider-only features:** Signal Studio තුළ Created/Owned සහ Joined Telegram destinations වෙන වෙනම පෙන්වයි; search, locally saved favorites සහ තෝරාගත් destinations කිහිපයකට publish කිරීම ඇත. Private groups account එකට access/join වී නැත්නම් title එකෙන් සොයාගත නොහැක.
>
> Published Signal Tracker එක entry/SL/TP, destinations, tracking mode සහ status පෙන්වයි. **LOAD TO FORM** තෝරා පරීක්ෂා කර **UPDATE POSTS** ඔබන විට original Telegram posts පමණක් edit වේ—MT5 orders වෙනස් නොවේ. Broker order එකක් වෙනස් කිරීමට වෙනම explicit ticket action අවශ්‍යයි.
>
> **MT5 AUTO (READ-ONLY)** opt-in quote monitoring පමණි; MT5 orders place/modify නොකරයි. පැහැදිලි status transition එකක් පමණක් Telegram post update කරයි. Missed/ambiguous move හෝ දිගු monitor gap එකක් manual review වෙත යයි. පරිගණකය සහ MT5 terminal විවෘතව තබන්න; demo account එකකින් monitor කළ හැක.
>
> Provider-only day/week/month/all-time performance සහ uploaded logo/name සහිත editable Excel/PDF exports ඇතුළත්. Trading Plan export එකට day-by-day sheet, editable formulas සහ වත්මන් daily-target achievement banner එක ඇතුළත්. Display resolution/DPI සඳහා Tk scaling ද වැඩිදියුණු කර ඇත.

## Historical v1.9.12 Local Desktop UI V4.8.4 — channel-source cleanup + MT5 diagnostics

> V4.8.1 යනු නොවෙනස් V4.7 Dashboard/MT5-history පදනම මත ඇති V4.8 optional Sinhala voice preview එකට unknown-message handler hotfix එකක් එක් කළ සංස්කරණයයි. V4.7 ZIP එක වෙනස් කර නැත. Windows voice/model/runtime/playback සාර්ථකයි කියා මෙහි තහවුරු කර නැත.
>
> **V4.8.2:** unknown Telegram post counter `IndexError` fix එක සහ plugged-in screen-off helper එක ඇතුළත්. `SCREEN-OFF-KEEP-LAPTOP-ON.bat` එකෙන් display එක විනාඩි 5කින් off වන අතර, AC power එකේ sleep `Never` වේ; battery sleep, hibernate සහ lid-close settings වෙනස් නොවේ. Charger එක සම්බන්ධ කර lid එක open තබන්න.
>
> Unknown-message fix එක unreadable post එකක් trade signal එකක් බවට පත් නොකරයි. `action=ignore` නම් MT5 වෙත order යවන්නේ නැත. Raw message එක බලන්න `unknown-signals.txt` භාවිතා කරන්න. 20-minute stale-message guard එලෙසම පවතී.
>
> **V4.8.4:** CHANNELS switch list එකේ දැනටමත් configure කර ඇති sources පමණක් පෙන්වයි; පැරණි journal/history entries සහ stale OFF keys active channel ලෙස නැවත පෙන්වන්නේ නැත. නම+Telegram ID එකටම එකතු කළ source එක එක වරක් friendly name එකෙන් පෙන්වයි. MT5 initialize/terminal/account කියවීම අසාර්ථක නම් error detail පෙන්වයි. MT5 කවුළුව විවෘතව තිබීම පමණක් API connection එක තහවුරු නොකරයි.

- **Dashboard** එකේ V4.6 summary overview එක (අද realized P&L, MT5 floating P&L, target, TP/SL/BE/manual ප්‍රතිඵල, best trade, කාලසීමා/චැනල් සාරාංශ) එලෙසම පවතී. ඊට අමතරව **OPEN TRADES** සහ **PENDING ORDERS** වෙනම ලැයිස්තු ඇත.
- **PENDING ORDERS** තුළ MT5 හි සෑම රැඳී ඇති LIMIT-channel order එකක්ම, channel/account, entry, current market, SL/TP, signal ලැබුණු වේලාව, order යැවූ වේලාව සහ ticket සමඟ පෙන්වයි. **OPEN TRADES** තුළ MARKET positions සහ trigger වූ LIMIT positions, live P&L සහ active වේලාව සමඟ පෙන්වයි. LIMIT order එක fill වූ පසු ඊළඟ live poll එකේ Pending වෙතින් ඉවත් වී Open Trades තුළ පෙනේ.
- **TRADE JOURNAL** තුළ **TRADE HISTORY**, **OPEN & PENDING**, **BEST TRADES**, **PROFIT FLOW**, සහ අලුත් **MT5 HISTORY** subpages ඇත. MT5 HISTORY එකෙන් connected terminal එක ලබාදෙන broker deals/positions, account balance/equity, realized/open P&L සහ journal එකට ගැළපූ channel P&L බලන්න. ගැළපෙන්නේ නැති trades “Manual / Other EA” ලෙස පෙන්වයි.
- Signal voice එක signal ලැබුණු වේලාව, MT5 account, order details/ticket කියයි; LIMIT එක trigger වූ විට activation වේලාවත් කියයි. Periodic voice summary එක capital (balance/equity) සහ channel realized P&L ද එක් කරයි. Sinhala live සංඛ්‍යා සඳහා matching female voice එකක් (Windows SAPI හෝ optional offline model) අවශ්‍යයි; English fallback නැත.
- **CHANNEL PROGRESS** සහ **MANUAL TRADES** ප්‍රධාන navigation එකේ වෙන වෙනම views ලෙස පවතී. Manual Trades හි අද open කළ සියලු non-EdgeQuant MT5 trades ඇත—වෙනත් EAs ඇතුළුව. Dashboard daily realized P&L එකට අද close කළ non-EdgeQuant trades සියල්ල එක්වේ; එම trade එක කලින් දවසක open වූවත් ගණන් ගනී. EdgeQuant trades දෙවරක් ගණන් නොගනී.
- Dashboard හි MT5 floating exposure එක සම්බන්ධිත MT5 ගිණුම්වල එකතුවයි. Daily Target සහ හඬ වාර්තාවේ realized/floating සංඛ්‍යා **EdgeQuant කළමනාකරණය කරන trades පමණක්** ඇතුළත් කරයි.
- **Dashboard → READ TODAY'S REPORT** ඔබා Sinhala දෛනික briefing එක දැන්ම කියවන්න; Telegram වෙත යවන්නේ නැහැ. කතා කරන report එක අද realized P&L, විවෘත ගනුදෙනු වල floating P&L, target මුදල/ප්‍රගතිය/තත්ත්වය, orders/fills/closes, TP/SL/BE/manual ප්‍රතිඵල සහ ගණන්, සහ හොඳම ගනුදෙනුවේ source channel, symbol, දිශාව, ප්‍රතිඵලය සහ pips කියයි.
- **Optional local model:** VOICE panel එකේ **INSTALL OFFLINE VOICE** තෝරා තහවුරු කළ විට වෙනම Python 3.11 environment එකක්, CPU PyTorch/Coqui TTS runtime එක සහ Dialog/UoM female `SinhalaVITS-TTS-F1` model එක (~1 GB) බාගත වේ. Model එක ZIP එකට ඇතුළත් කර නැහැ. Model/runtime download සඳහා internet අවශ්‍යයි; dynamic report synthesis සහ playback පරිගණකයේම සිදු වන අතර වාර්තා/ලාභ/මිල/චැනල් පෙළ පිටතට යවන්නේ නැහැ.
- Setup එක අවසන් වූ පසු sample එකක් synthesize කර Windows audio playback පරීක්ෂා කරයි. EdgeQuant නැවත ආරම්භ කර LANGUAGE `SI` තෝරා REFRESH ඔබන්න; TEST භාවිතා කරන්න. Voice report තත්ත්වය queued/dispatched සහ actually played යන දෙක වෙනස් කර පෙන්වයි. Sinhala female voice එකක් සූදානම් නැත්නම් dynamic figures static clip හෝ English වෙත මාරු නොකරයි.
- Installer/runtime/checkpoint compatibility, model inference, Sinhala pronunciation quality, hardware performance සහ Windows playback මෙම sandbox එකේ පරීක්ෂා කර නැහැ. ගැටලුවක් නම් installer window එකේ දෝෂය බලන්න; V4.8 තවම Windows-validated voice release එකක් නොවේ. සම්පූර්ණ විස්තරය `SINHALA-OFFLINE-VOICE.md` තුළ ඇත.
- Pending entry/SL/TP හෝ open position SL/TP/break-even edits **local desktop පමණක්** භාවිතයෙන්, එක් තෝරාගත් ticket එකකට, තහවුරු කිරීමෙන් පසු සිදු වේ. Web monitor එක read-only ය.
- Telegram incoming-only ආරක්ෂාව පවතී; තමන්ගේ outgoing posts මත trade නොකරයි. Telegram reconnect/catch-up, duplicate/age/TP-hit සහ අනෙකුත් safety checks වෙනස් කර නැත.
- දෙකේ-order behavior පවතී: Layer 1 target Dashboard වෙතින් පාලනය කළ හැක (default +100 pips); Layer 2 නිවැරදි signal TP භාවිතා කරයි. Profit-protecting BE සහ Windows **system awake / display timeout allowed** option එකත් පවතී.
- V4.7 base offline validation remains historical: desktop **280/280**, engine **515/515**, parser **41/41**, fake-MT5 **4/4**, web-agent **10/10**. Current V5.1.1 checks, historical V5.0.0/V4.9.0/V4.8.4 details සහ Windows/DPAPI/model limitations සඳහා `SOURCE-VALIDATION.md` බලන්න.

## 1. Telegram API credentials — each client enters their own

Every client must use the `api_id` and `api_hash` from their own Telegram account's app page. Do not ship your personal API keys inside the client package or share them with customers. The app has a dedicated setup dialog so clients do not need to edit Python files or `config.json`.

1. Launch the current desktop with `EDGEQUANT-APP.bat`, then press **LOGIN → API SETUP** (or **Settings → TELEGRAM API SETUP**). Older standalone `bot.py` / `telegram_listener.py` launchers are separate legacy paths and do not use this dialog.
2. Press **OPEN TELEGRAM API PAGE**. At `https://my.telegram.org/apps`, sign in with the Telegram account this PC will use. Under **API development tools**, create an app if needed and copy its API ID (number) and API hash (32-character value). This is **not** a BotFather bot token.
3. Enter both values in the app and press **SAVE SECURELY**. The app validates them and encrypts them with Windows DPAPI for the current Windows user, storing the encrypted file under `%LOCALAPPDATA%\EdgeQuant`. The setup action itself makes no Telegram request and does not upload the keys to EdgeQuant. The keys are used with Telegram only after the user presses **SEND CODE**.
4. Close the API setup dialog, enter the phone number and press **SEND CODE**. The login code arrives inside Telegram. Enter it in the app; enter a 2FA password only if Telegram asks. Then choose the joined source channels in **CHANNELS**.

The encrypted credential file is tied to that Windows user; it cannot be copied to a different PC or Windows account and decrypted there. If DPAPI cannot read a saved value, use **API SETUP** again on that PC. Do not put API keys in `edgequant_auto.py`, `config.json`, screenshots, batch files, chat messages, or the ZIP/Git package. Never send a Telegram login code, 2FA password, or `.session` file to anyone.

For existing installations, the local environment variables `EDGEQUANT_API_ID` and `EDGEQUANT_API_HASH` remain supported as a fallback. The app prefers credentials saved in its Windows DPAPI store. To configure the fallback manually, use the customer's own values in a PowerShell window and restart EdgeQuant afterward:

```powershell
setx EDGEQUANT_API_ID "YOUR_NUMERIC_API_ID"
setx EDGEQUANT_API_HASH "YOUR_32_CHARACTER_API_HASH"
```

Source/channel setup remains stopped-bot-only: do not scan while a bot or another login dialog is active. Source scanning checks chat metadata for chats the signed-in account already joined; it does not read message history or leave/delete Telegram groups when a source is removed.

## 2. MT5 gold symbol choice — all signal groups

Signal text `GOLD` is normalized to canonical `XAUUSD`. The actual tradable name can differ on each saved MT5 account. The BROKERS tab uses your existing saved account configuration; its add/remove account form is removed. If an app-saved account exists with no static account configured, that saved list becomes the default, without adding a phantom `MAIN` account. In **BROKERS → XAUUSD BROKER SYMBOL**, choose the saved account and its exact name: `XAUUSD`, `XAUUSDm`, `XAUUSDc`, or type another exact Market Watch symbol. **AUTO** uses the existing fallback resolver. Press **SAVE SYMBOL**. This account-level choice applies to every user-added signal group routed to that account; it does not change each channel's LIMIT/MARKET route.

Use the exact spelling shown in that account's MT5 Market Watch (the screenshot provided shows `XAUUSDc`). An explicit choice is checked before each trade; if that symbol is absent, that account is skipped rather than silently substituting another suffix. No order is sent when you choose/save a symbol. Choices are stored separately in `edgequant_broker_symbols.json`; the selector does not clear channels, channel routes, Telegram credentials, or other account settings.

Any placed signal missing either SL or TP is held for manual review for every added signal group, except explicit MARKET/NOW/INSTANT instructions that retain the existing auto-protection path. A later fully protected post is handled as its own Telegram message; old messages are not replayed. The normal freshness, exact message-ID duplicate, TP-hit, account/channel, LIVE, risk, and broker checks remain.

## Cloud/Provider-Receiver accounts — දැනට local UI පමණයි

දැනට Supabase/Cloud සම්බන්ධතාව හිතාමතාම අක්‍රිය කර ඇත. Cloud login form හෝ database requests නොමැත; cloud request runner එක network call එකක් යැවීමට පෙර නවතී. මේ අදියරේදී Supabase project, URL/key, SQL schema, SMTP හෝ email confirmation සකස් කරන්න එපා. Cloud සම්බන්ධ කිරීම ගැන ඔබ පසුව දෙන උපදෙස් අනුව එය වෙනම ක්‍රියාත්මක කරමු.

1. EdgeQuant ආරම්භ කළ විට WELCOME පිටුවෙන් **SIGNAL PROVIDER** හෝ **SIGNAL RECEIVER** තෝරන්න. **OPEN SELECTED WORKSPACE** ඔබා එම local workspace එකට යන්න. මේ තේරීම UI එක පමණක් පාලනය කරයි; එය cloud-verified login එකක් හෝ account role එකක් නොවේ.
2. **Provider** workspace එකේ **SIGNAL STUDIO** tab එකෙන් validated signal එකක් සකස් කර ඔබේ Telegram ගිණුමට පෙනෙන/join වී ඇති destinations වෙත publish කළ හැක. මෙය Telegram integration එකයි—Supabase group sharing හෝ cloud publish කිරීමක් නොවේ. Cloud group publishing කොටස planned/disabled ලෙස පෙන්වයි.
3. **Receiver** workspace එකෙන් local **CHANNELS** source list සහ Dashboard ашиг කර Telegram sources болон local processing тохируම් කරන්න. Signal processing/MT5 order safety нь පවතින local TEST RUN/LIVE flow එක හරහාම යයි. Receiverට Provider-ийн SIGNAL STUDIO නොපෙන්වයි.
4. **LOCAL PROFILE** tab එකේ `CLOUD SERVICES • NOT CONNECTED IN THIS STAGE` පණිවිඩය පෙන්වයි. එහි login, group sync, shared feed හෝ approval controls නැත. එම පිටුවෙන් **CHANGE WORKSPACE** තෝරා Provider/Receiver අතර මාරු විය හැක.
5. Cloud service enable කිරීමට අවශ්‍ය උපදෙස්, account/email, project, security සහ workflow තීරණ පසුව ලබාදෙන්න. එතෙක් Supabase/API credentials කිසිවක් app එකට ඇතුළත් කිරීමට අවශ්‍ය නැහැ.

## 3. Local trading ආරක්ෂාව

- **Daily Target**, compound/stop-after විකල්ප සහ periodic update controls සියල්ල **Dashboard → DAILY TARGET** කොටසේ තබා ඇත. ඒවා සොයන්න Settings tab එකට යන්න අවශ්‍ය නැහැ.
- LIVE ට පෙර **TEST RUN** අනිවාර්යයෙන් පරීක්ෂා කරන්න. TEST RUN එකෙන් සැබෑ orders යවන්නේ නැහැ.
- **START** ඔබන විට account/risk review එකක් සහ checkbox acknowledgement එකක් පෙන්වයි. Startup එකේ `LIVE` කියන වචනය ටයිප් කිරීම තවදුරටත් අවශ්‍ය නැහැ.
- Telegram Studio හි **PUBLISH + PROCESS** තේරීම සඳහා, engine එක LIVE නම් වෙනම `LIVE` තහවුරු කිරීමක් තවම අවශ්‍යයි. Destinations කිහිපයකට publish කළත් local processing එක signal එකකට එක් වරක් පමණක් සිදු කර duplicate orders අවම කරයි.
- **Dashboard → DAILY LOSS CAP** එකේ 0=OFF ලෙස cap එක සුරකින්න. **UNLOCK TODAY** ක්‍රියාත්මක වන්නේ loss limit එක hit වූ විට පමණයි; තහවුරු කළ unlock එක අදට පමණක් වලංගුයි, හෙට protection නැවත ක්‍රියාත්මක වේ.
- මෙම software එක financial advice නොවේ. LIVE සක්‍රිය කිරීමට පෙර MT5 account/server, symbol mapping, risk/lot size, SL/TP සහ source channels පරීක්ෂා කරන්න.

## 4. Cloud, offline භාවිතය සහ licensing

අනාගත architecture එක hybrid ලෙස සැලසුම් කර ඇත: Telegram sessions සහ MT5 execution Windows PC එකේ local ලෙස ක්‍රියා කරයි; cloud accounts, groups සහ shared provider signals සඳහා internet අවශ්‍ය වේ. **නමුත් මෙම build එකේ Cloud සම්බන්ධතාව disabled** бөгөөд UI එකෙන් cloud session හෝ network request නිර්මාණය නොවේ. Cloud කොටස ඔබ පසුව දෙන උපදෙස් අනුව පමණක් එක් කරමු.

අවශ්‍ය වාණිජ license policy එක **එක් lifetime license එකකට එක් Windows PC එකක්, offline activation සමඟ** යන්නයි. එම licensing/activation ක්‍රමය v1.9.12 තුළ තවම implement කර නැහැ. License module එක හදා පරීක්ෂා කරන තුරු lifetime license, one-PC enforcement හෝ cloud groups සඳහා සම්පූර්ණ offline access ඇතැයි කියන්න එපා. Offline activation සඳහා revocation/transfer ප්‍රතිපත්තියක් සහ recovery ක්‍රියාවලියක් ද අවශ්‍යයි.

## 5. පරීක්ෂා කිරීම සහ Windows EXE සෑදීම

V5.1.4 හි `BUILD-EXE.bat` guard එක `desktop 1.9.12 UI-V5.1.4` build එක පිළිගෙන `provider_studio.py`, Pillow (image plugins ඇතුළුව), openpyxl සහ `et_xmlfile` ඇතුළත් කරයි. Build එකට පෙර Pillow මගින් bundled logo එක කියවිය හැකිද පරීක්ෂා කරයි; අවසානයේ frozen EXE එකෙන් Provider, daily EOD සහ Plan Excel exports logo embed කර ඇති බවට ZIP media ද ඇතුළුව create/reopen smoke test කරයි. Logo/Pillow import එක තවම fail වුවහොත් `xlsx-selfcheck.log` තුළ හේතුව සහ traceback සුරැකේ. මෙම source environment එකේ Windows/PyInstaller EXE එක ධාවනය කර නැහැ; Windows PC එකක සාර්ථකව build/verify කළ පසු පමණක් `dist/EdgeQuantSentinel` සම්පූර්ණ folder එක බෙදාහරින්න.

App folder එකෙන් පහත commands ධාවනය කරන්න:

```powershell
python edgequant_auto.py --selftest
python edgequant_desktop.py --selfcheck
python -m unittest -v test_provider_studio_v510.py test_sinhala_voice_worker.py
python edgequant_desktop.py --xlsx-selfcheck
python edgequant_check.py
python edgequant_web_agent.py --selftest
```

Windows package එක සෑදීමට dependencies සකසා `BUILD-EXE.bat` ධාවනය කරන්න. සාදන EXE එකත්, target Windows version එකේ Telegram/MT5 live behavior එකත් වෙනම පරීක්ෂා කළ යුතුයි. v1.9.12 පරීක්ෂා කරන අතර පැරණි installation එක වෙනස් නොකර තබාගන්න.


## V5.1.1 voice, brand, polls සහ file posts
- Dynamic Sinhala report එක කථා කිරීමට Windows එකේ female Sinhala SAPI voice එකක් හෝ app එකේ `INSTALL OFFLINE VOICE` button එකෙන් optional local model එක ස්ථාපනය කර test කර තිබිය යුතුයි. Model එක නොමැති විට app එක Sinhala report එක English වලින් කියන්නේ නැහැ; voice panel එක warning එක පෙන්වයි.
- Signal Composer හි default bundled logo එක නව EdgeQuant brand lockup එකයි. Custom logo preference එක වෙනස් කරන්නේ නැහැ.
- Provider `POST / POLL` පිටුවේ `ATTACH FILE` භාවිතයෙන් file එකක් සහ optional caption එකක් තෝරලා යැවීමට පෙර destinations තහවුරු කරන්න. Poll එක අසාර්ථක නම් දැන් destination එකේ සම්පූර්ණ error එක local log එකේ පෙන්වයි.
