#!/usr/bin/env python3
# -*- coding: ascii -*-
"""EdgeQuant Sentinel - FILE / VERSION CHECK.

Double click EDGEQUANT-VERSION.bat (or run:  python edgequant_check.py).
It only READS files - it never starts the bot and never sends anything.

It tells you, in one screen:
  * is edgequant_auto.py the NEW version (or the old one that crashes) ?
  * is edgequant_desktop.py the NEW version ?
  * are the new TABS (PROFIT CALENDAR / BROKERS) inside ?
  * are the logo / watermark files there ?
  * is MetaTrader5 + telethon + Pillow installed ?
"""
import ast
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
NEED = (1, 9, 12)                   # v1.9.12  selected Telegram sources + UI safety fixes


def say(text=""):
    print(text)


def version_of(src, name="VERSION"):
    if not src:
        return ""
    m = re.search(r'(?m)^%s\s*=\s*"([^"]+)"' % name, src)
    return m.group(1) if m else ""


def vnum(text):
    try:
        return tuple(int(x) for x in re.findall(r"\d+", str(text))[:3])
    except Exception:
        return (0,)


def help_strings(src):
    """Every add_argument(help=...) string of a file - [] when unreadable."""
    out = []
    try:
        tree = ast.parse(src)
    except Exception:
        return out
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node.func, "attr", "") == "add_argument":
            for kw in node.keywords:
                if kw.arg == "help" and isinstance(kw.value, ast.Constant) \
                        and isinstance(kw.value.value, str):
                    out.append((node.lineno, kw.value.value))
    return out


def main():
    say("=" * 74)
    say("   EDGEQUANT  SENTINEL   -   FILE  /  VERSION  CHECK")
    say("=" * 74)
    say(f"   folder : {HERE}")
    say(f"   python : {sys.version.split()[0]}   ({sys.executable})")
    say("-" * 74)

    problems = []

    # ------------------------------------------------------------ engine ----
    auto_file = HERE / "edgequant_auto.py"
    auto = auto_file.read_text(encoding="utf-8", errors="replace") if auto_file.exists() \
        else None
    if auto is None:
        say("   [ X ] edgequant_auto.py        NOT FOUND in this folder")
        problems.append("edgequant_auto.py MISSING - you are in the wrong folder ?")
    else:
        ver = version_of(auto)
        is_new = vnum(ver) >= NEED
        say(f"   [{'OK ' if is_new else ' X '}] edgequant_auto.py"
            f"        v{ver}          (need v{'.'.join(map(str, NEED))})")
        if not is_new:
            problems.append("edgequant_auto.py is older than v1.9.12 - extract the new ZIP to a separate folder")
        # the real test: can argparse build its help texts on THIS python ?
        broken = []
        for line, text in help_strings(auto):
            try:
                text % {"prog": "x"}
            except Exception as exc:
                broken.append(f"line {line}: {exc}")
        if broken:
            say("   [ X ] the old argparse bug is STILL in edgequant_auto.py:")
            for b in broken[:4]:
                say(f"         {b}")
            problems.append("edgequant_auto.py still has a bad --help string -> every "
                            ".bat file will crash")
        else:
            say("   [OK ] --help texts are safe (no %-format crash)")
        weekend_limit_queue_ok = all(token in auto for token in (
            "WEEKEND_LIMIT_QUEUE_POLICY", "WEEKEND_LIMIT_QUEUE_MAX_AGE_HOURS = 72.0",
            "initial_age_limit = signal_age_limit_min(category)",
            "signal_deferred_age_limit_min", "queue_policy=queue_policy",
            "deferred_age_limit if weekend_limit_deferred",
            "Weekend LIMIT queue expired"))
        say(f"   [{'OK ' if weekend_limit_queue_ok else ' X '}] weekend LIMIT queue persists/rechecks to 72h with fail-closed expiry")
        if not weekend_limit_queue_ok:
            problems.append("weekend LIMIT deferred queue policy or revalidation is missing/incomplete")

    # ----------------------------------------------------------- desktop ----
    desk_file = HERE / "edgequant_desktop.py"
    desk = desk_file.read_text(encoding="utf-8", errors="replace") if desk_file.exists() \
        else None
    if desk is None:
        say("   [ X ] edgequant_desktop.py     NOT FOUND")
        problems.append("edgequant_desktop.py MISSING")
    else:
        build = version_of(desk, "APP_BUILD")
        is_new = vnum(build) >= NEED
        say(f"   [{'OK ' if is_new else ' X '}] edgequant_desktop.py"
            f"     {build}       (need {'.'.join(map(str, NEED))})")
        if not is_new:
            problems.append("edgequant_desktop.py is older than v1.9.12 - use the separate new folder")
        ui_v513 = "UI-V5.1.13" in build
        say(f"   [{'OK ' if ui_v513 else ' X '}] current UI/build label UI-V5.1.13")
        if not ui_v513:
            problems.append("desktop is missing the current V5.1.13 strategy build label")
        for part, label in (("_build_calendar", "PROFIT CALENDAR tab"),
                            ("_build_brokers", "BROKERS tab"),
                            ("_build_preview", "SIGNAL PREVIEW tab"),
                            ("_build_agent", "AI AGENT tab"),
                            ("_paint_live", "LIVE TRADES board")):
            _ = part
            have = part in desk
            say(f"   [{'OK ' if have else ' X '}] {label}"
                f"{'' if have else '            (missing - old desktop file)'}")
        for part, label in (("def scan_telegram(self)", "CHANNELS tab: SCAN TELEGRAM"),
                            ("filter_telegram_dialogs", "live channel-name suggestions"),
                            ("Stop the bot first, then scan.", "bot must stop before scan"),
                            ("Close the Telegram LOGIN dialog before scanning.", "pending LOGIN dialog guard"),
                            ("E.acquire_singleton()", "Telegram singleton lock"),
                            ("ADD AS LIMIT", "add as LIMIT"),
                            ("ADD AS MARKET", "add as MARKET"),
                            ("def remove_channel_dialog(self)", "EdgeQuant-only source removal"),
                            ("def _build_studio(self, parent)", "Telegram Studio tab"),
                            ("PUBLISH + PROCESS", "per-signal publish/process choice"),
                            ("def _confirm_studio_live", "typed LIVE gate for Studio processing"),
                            ("ttk.Combobox(look", "explicit UI language/theme/voice selectors"),
                            ("def bilingual_welcome", "bilingual personalized welcome"),
                            ("def _build_guide", "role-aware bilingual Guide / Upades tab"),
                            ("POST / POLL", "Provider text post and poll tab"),
                            ("telegram_studio_send_poll", "Telegram poll helper"),
                            ("studio_live_market_tree", "Provider live Market view"),
                            ("studio_live_limit_tree", "Provider pending Limit view"),
                            ("def apply_layer1_target", "Dashboard-configurable Layer 1 target"),
                            ("def apply_auto_be", "Dashboard AUTO BE ON/OFF master toggle")):
            have = part in desk
            say(f"   [{'OK ' if have else ' X '}] {label}"
                f"{'' if have else '            (missing - old desktop file)'}")
            if not have:
                problems.append(f"{label} missing - extract the complete v1.9.12 package")

    # ------------------------------------------------------- account/cloud ---
    cloud_file = HERE / "edgequant_cloud.py"
    cloud = cloud_file.read_text(encoding="utf-8", errors="replace") if cloud_file.exists() else ""
    for part, label in (("EMAIL-VERIFIED ACCOUNT", "ACCOUNT / CLOUD tab"),
                        ("def cloud_register", "provider/receiver registration"),
                        ("def cloud_resend_confirmation", "resend verification email"),
                        ("def cloud_password_reset", "password reset email"),
                        ("def cloud_request_public_group", "public-group access requests"),
                        ("def _build_role_entry", "first-screen Provider/Receiver role chooser"),
                        ("def _activate_cloud_workspace", "verified role-specific workspace routing"),
                        ("def _apply_role_workspace", "role-based tab access"),
                        ("SIGNAL PROVIDER STUDIO", "dedicated Provider signal studio"),
                        ("def cloud_publish_selected_groups", "multi-group Provider publishing"),
                        ("self.provider_dest_list", "Provider group destination selector"),
                        ("def cloud_process_selected_signal", "receiver local-processing action"),
                        ("def cloud_export_group_report", "shareable group HTML report export"),
                        ("EXPORT GROUP REPORT  \u2022  HTML", "group report export button"),
                        ("def build_provider_report_html", "provider performance report builder"),
                        ("realized_pnl_usd", "recorded USD outcome data"),
                        ("realized_pips", "recorded actual pips data"),
                        ("AUTO-REFRESH WHILE OPEN (~6 SEC)", "cloud signal polling while open"),
                        ("asyncio.run_coroutine_threadsafe(dispatch(), runner.loop)",
                         "shared signals run on the engine loop")):
        have = part in desk
        say(f"   [{'OK ' if have else ' X '}] {label}")
        if not have:
            problems.append(f"{label} missing - rebuild the v1.9.12 desktop")
    for part, label in (("def resend_confirmation", "Supabase confirmation resend"),
                        ("def verify_email_otp", "in-app signup OTP verification"),
                        ("def send_password_reset", "Supabase password reset"),
                        ("def list_signals", "group-scoped cloud signal query"),
                        ("def list_group_signal_updates", "group-scoped signal-update query"),
                        ("service_role key is not allowed", "service-role key rejection"),
                        ("def request_join", "public-group request RPC client")):
        have = part in cloud
        say(f"   [{'OK ' if have else ' X '}] {label}")
        if not have:
            problems.append(f"{label} missing - update edgequant_cloud.py")
    schema_file = HERE / "supabase" / "schema.sql"
    schema = schema_file.read_text(encoding="utf-8", errors="replace") if schema_file.exists() else ""
    schema_ok = (schema.lower().count("enable row level security") >= 7
                 and "request_public_provider_group" in schema
                 and "respond_provider_group_request" in schema)
    say(f"   [{'OK ' if schema_ok else ' X '}] Supabase RLS + public access/approval RPCs")
    if not schema_ok:
        problems.append("Supabase RLS schema or access-request RPCs missing/incomplete")

    # ------------------------------------------------------------- extras ---
    say("-" * 74)
    for f, label in (("edgequant-logo-small.png", "logo (header)"),
                     ("edgequant-watermark.png", "logo watermark (background)"),
                     ("edgequant-icon.ico", "window / taskbar icon"),
                     ("provider_studio.py", "Provider monitoring/export helpers"),
                     ("requirements.txt", "Python dependencies (Excel/logo exports)"),
                     ("SETUP.md", "Sinhala setup guide"),
                     ("RELEASE-NOTES-1.9.12.txt", "v1.9.12 development notes"),
                     ("RELEASE-NOTES-1.9.12-V5.1.13-TELEGRAM-BASIC-GROUP-SEND.txt", "V5.1.13 Telegram basic-group notes"),
                     ("SOURCE-VALIDATION.md", "source build validation and remaining scope")):
        say(f"   [{'OK ' if (HERE / f).exists() else ' - '}] {label:<26} {f}")

    build_text = (HERE / "BUILD-EXE.bat").read_text(encoding="ascii", errors="replace") \
        if (HERE / "BUILD-EXE.bat").exists() else ""
    desktop_source = (HERE / "edgequant_desktop.py").read_text(encoding="utf-8", errors="replace") \
        if (HERE / "edgequant_desktop.py").exists() else ""
    provider_source = (HERE / "provider_studio.py").read_text(encoding="utf-8", errors="replace") \
        if (HERE / "provider_studio.py").exists() else ""
    client_batch = (HERE / "BUILD-CLIENT-INSTALLER.bat").read_text(encoding="utf-8", errors="replace") \
        if (HERE / "BUILD-CLIENT-INSTALLER.bat").exists() else ""
    provider_build_ok = ("UI-V5.1.13" in build_text and "provider_studio.py" in build_text
                        and "openpyxl" in build_text and "et_xmlfile" in build_text
                        and "Pillow" in build_text and "from PIL import Image" in build_text
                        and "--hidden-import PIL.Image" in build_text
                        and "--collect-submodules PIL" in build_text and "--collect-all PIL" in build_text
                        and "--xlsx-selfcheck" in build_text
                        and "provider and plan Excel exports opened successfully with logos" in build_text
                        and "edgequant-logo.png" in build_text
                        and "logo_path = BRAND_LOGO if BRAND_LOGO.is_file() else LOGO_SMALL" in desktop_source
                        and "xl/media/" in desktop_source
                        and "brand_name=provider_name" in provider_source
                        and "_set_software_footer" in provider_source
                        and "footer.text = \"EdgeQuant Sentinel\"" in provider_source
                        and "--mt5-import-selfcheck" in build_text
                        and "--hidden-import MetaTrader5._core" in build_text
                        and "--collect-binaries MetaTrader5" in build_text
                        and all(token in desktop_source for token in (
                            "edgequant_provider_journal.json", "provider_manual_trade_ids",
                            "magic=0", "PROVIDER LAYER 1 QUICK TP (PIPS)",
                            "quick_tp_pips=provider_quick_tp_pips",
                            "Replace the brand in the first line with the selected destination name"))
                        and "linked_trade_ids" in provider_source
                        and "test_signal_format_examples.py" in client_batch
                        and "test_followup_management.py" in client_batch
                        and "match_followup_entry_records" in (HERE / "edgequant_auto.py").read_text(encoding="utf-8", errors="replace")
                        and "chat_id=chat_id" in (HERE / "edgequant_auto.py").read_text(encoding="utf-8", errors="replace")
                        and auto is not None
                        and 'new, label = price - step, "down"' in auto
                        and 'new, label = price + step, "up"' in auto
                        and "NO_OPPOSITE_TRADES = False" in auto
                        and "opposite-direction hedge blocking is disabled by owner request" in auto
                        and 'f"{configured_key} chat"' in auto
                        and "test_configured_channel_chat_suffix_uses_authoritative_price_run_exception_exactly" in (HERE / "test_signal_format_examples.py").read_text(encoding="utf-8", errors="replace")
                        and "test_valid_sell_format_is_not_skipped_after_sixty_six_pip_market_move" in (HERE / "test_signal_format_examples.py").read_text(encoding="utf-8", errors="replace")
                        and "Owner removed discretionary price-run skips for parsed trade signals" in auto
                        and "4038.0, 4219.0" in (HERE / "test_signal_format_examples.py").read_text(encoding="utf-8", errors="replace")
                        and "4043.0, 4021.0" in (HERE / "test_signal_format_examples.py").read_text(encoding="utf-8", errors="replace")
                        and "edgequant_auto.py --selftest" in client_batch)
    say(f"   [{'OK ' if provider_build_ok else ' X '}] V5.1.13 strategy/reconnect tests + Provider build checks")
    if not provider_build_ok:
        problems.append("Build/source checks must include V5.1.13 strategy/reconnect tests, Provider journal isolation/manual links, independent Layer 1, branded exports, Pillow logos, and MetaTrader5 _core verification")
    client_iss = (HERE / "EdgeQuantSentinel-Client.iss").read_text(encoding="utf-8", errors="replace") \
        if (HERE / "EdgeQuantSentinel-Client.iss").exists() else ""
    client_scrub = (HERE / "SCRUB-CLIENT-DIST.ps1").read_text(encoding="utf-8", errors="replace") \
        if (HERE / "SCRUB-CLIENT-DIST.ps1").exists() else ""
    client_docs = (HERE / "CLIENT-SETUP-README.md").read_text(encoding="utf-8", errors="replace") \
        if (HERE / "CLIENT-SETUP-README.md").exists() else ""
    reconnect_src = (HERE / "edgequant_auto.py").read_text(encoding="utf-8", errors="replace") \
        if (HERE / "edgequant_auto.py").exists() else ""
    reconnect_test = HERE / "test_telegram_reconnect.py"
    reconnect_ok = (all(token in reconnect_src for token in (
                            "AUTO_RECONNECT = True", "telegram_transient_connection_error",
                            "phase=\"reconnecting\"", "Telegram reconnected - watching the channels again"))
                    and reconnect_test.is_file()
                    and "tg_login_with_timeout" in reconnect_test.read_text(encoding="utf-8", errors="replace"))
    say(f"   [{'OK ' if reconnect_ok else ' X '}] mandatory Telegram auto-reconnect + offline regression tests")
    if not reconnect_ok:
        problems.append("Telegram must retry temporary saved-session/startup and active-listener disconnects automatically")
    client_build_ok = (all(token in client_batch for token in (
                            "BUILD-EXE.bat", "SCRUB-CLIENT-DIST.ps1", "ISCC.exe",
                            "EdgeQuant-Sentinel-Client-Setup.exe",
                            "python -m unittest -v test_telegram_reconnect.py test_signal_format_examples.py test_followup_management.py"))
                       and all(token in client_iss for token in (
                            "PrivilegesRequired=lowest", "{localappdata}\\Programs",
                            "*.py,*.pyw"))
                       and all(token in client_scrub for token in (
                            "edgequant_auto.py", "edgequant_*.json", "*.session*",
                            "config.json", "credentials.json",
                            "($_.Extension -in @('.py', '.pyw'))"))
                       and "edgequant_user_settings.json" in desktop_source
                       and "apply_desktop_settings" in desktop_source
                       and "Do not distribute a client installer" in client_docs)
    say(f"   [{'OK ' if client_build_ok else ' X '}] source-scrubbed Windows client installer build kit (not Windows-tested here)")
    if not client_build_ok:
        problems.append("Client installer kit must bundle per-user settings, scrub source/secrets, and install per-user")
    requirements_text = (HERE / "requirements.txt").read_text(encoding="utf-8", errors="replace") \
        if (HERE / "requirements.txt").exists() else ""
    send_as_source = (HERE / "edgequant_auto.py").read_text(encoding="utf-8", errors="replace")
    send_as_tests = (HERE / "test_signal_format_examples.py").read_text(encoding="utf-8", errors="replace")
    send_as_ok = (all(token in send_as_source for token in (
                          "send_as=chat", "never fall back to the user",
                          "def _telegram_studio_is_basic_group", "def _telegram_studio_is_group_peer",
                          "if _telegram_studio_is_group_peer(chat):",
                          "Public groups/channels retain the established destination Send As check"))
                  and "test_private_basic_group_uses_selected_account_without_send_as_fallback" in send_as_tests
                  and "test_private_megagroup_uses_signed_in_account_without_send_as" in send_as_tests
                  and "telethon>=1.41,<2" in requirements_text
                  and '"telethon>=1.41,<2"' in build_text)
    say(f"   [{'OK ' if send_as_ok else ' X '}] private groups use signed-in account; public channels remain Send As-gated")
    if not send_as_ok:
        problems.append("Telegram Studio must allow account-sent private group posts, retain public channel Send As checks, and package Telethon >=1.41")
    premium_monitor_ok = all(token in desktop_source for token in (
        "BROKER CONNECTION  \u00b7  LIVE XAUUSD SPREAD", "def _request_dashboard_quote_snapshot",
        "def apply_dashboard_spread_limit", "def _paint_execution_review_queue",
        "def _dashboard_execute_review", "JOIN & ADD GROUP"))
    say(f"   [{'OK ' if premium_monitor_ok else ' X '}] live broker/spread dashboard, configurable guard, Manual Review actions, private-group join")
    if not premium_monitor_ok:
        problems.append("Premium broker/spread dashboard, Manual Review, or private-group join workflow is incomplete")
    voice_clip = HERE / "voice" / "si" / "update.wav"
    voice_copy_ok = (r'xcopy /E /I /Y "voice" "dist\EdgeQuantSentinel\voice"' in build_text
                     and r'voice\si\update.wav" goto fail' in build_text
                     and 'copy /y "edgequant_sinhala_voice_worker.py"' in build_text
                     and 'copy /y "INSTALL-SINHALA-FEMALE-VOICE.bat"' in build_text)
    say(f"   [{'OK ' if voice_clip.is_file() else ' X '}] Sinhala update clip  {voice_clip.relative_to(HERE)}")
    say(f"   [{'OK ' if voice_copy_ok else ' X '}] EXE copies Sinhala assets, local worker and optional installer")
    if not voice_clip.is_file():
        problems.append("voice/si/update.wav is missing")
    if not voice_copy_ok:
        problems.append("BUILD-EXE.bat does not copy/check Sinhala assets and optional worker/installer")
    voice_worker = HERE / "edgequant_sinhala_voice_worker.py"
    voice_installer = HERE / "INSTALL-SINHALA-FEMALE-VOICE.bat"
    voice_doc = HERE / "SINHALA-OFFLINE-VOICE.md"
    voice_optional_ok = all(path.is_file() for path in (voice_worker, voice_installer, voice_doc))
    say(f"   [{'OK ' if voice_optional_ok else ' X '}] offline Sinhala voice worker / installer / notice")
    if not voice_optional_ok:
        problems.append("one or more offline Sinhala voice integration files are missing")

    # ---- v1.8.0 + v1.9.12: voice, channel onboarding, Studio + cloud -----
    vdir = HERE / "voice"
    clips = sorted(vdir.glob("*.wav")) if vdir.exists() else []
    say(f"   [{'OK ' if clips else ' - '}] {'voice clips (TP/SL/BE)':<26} voice\\  "
        f"({len(clips)} file(s))")
    NEW_FEATS = (("def weekend_flat_check", "friday flat (weekend gap guard)"),
                 ("def news_block_now", "news guard (NFP / CPI / FOMC)"),
                 ("def loss_streak_guard", "consecutive-SL guard hook"),
                 ("MAX_CONSECUTIVE_SL = 0", "consecutive-SL entry pause disabled"),
                 ("def trading_plan", "AI trading plan tab"),
                 ("def channel_cfg", "per channel settings"),
                 ("def voice_sentence", "AI voice (clips + Windows voice)"),
                 ("def stream_board_stats", "animated profit flow board"),
                 ("PDF_DARK = True", "dark institutional PDF"),
                 ("def extra_charts" if False else "def excel_charts", "excel charts"),
                 ("def real_pl_sync", "real P&L (commission + swap)"),
                 ("async def telegram_scan_dialogs", "Telegram chat scan (names + IDs)"),
                 ("async def telegram_studio_create_chat", "Telegram Studio group/channel creation"),
                 ("async def telegram_studio_invite_members", "manual contact invites (rate-limited)"),
                 ("async def telegram_studio_send_signal", "branded signal publishing"),
                 ("async def telegram_studio_send_message", "selected-destination plain-text posts"),
                 ("async def telegram_studio_send_poll", "selected-destination Telegram polls"),
                 ("async def telegram_studio_edit_signal", "edit tracked Studio posts"),
                 ("async def telegram_studio_pending_join_requests", "join-request review"),
                 ("telegram_studio_username_suggestion", "public username suggestion"),
                 ("CHANNEL_ID_NAMES", "source name/ID link for removal"),
                 ("_TELEGRAM_CREDENTIALS_FILENAME", "Telegram API credentials use per-client DPAPI storage"),
                 ("English fallback is disabled", "Sinhala voice has no English fallback"),
                 ("def local_sinhala_voice_speak", "optional offline female Sinhala TTS worker"),
                 ("def voice_last_dispatch", "truthful queued-vs-played voice status"))
    src = (HERE / "edgequant_auto.py").read_text(encoding="utf-8", errors="replace")
    for needle, label in NEW_FEATS:
        _version = "v1.9.12" if ("telegram_scan" in needle or "telegram_studio" in needle
                                   or "CHANNEL_ID_NAMES" in needle or "username_suggestion" in needle
                                   or "EDGEQUANT_API_ID" in needle or "_TELEGRAM_CREDENTIALS_FILENAME" in needle
                                   or "English fallback" in needle
                                   or "local_sinhala_voice_speak" in needle
                                   or "voice_last_dispatch" in needle) else "v1.8.0"
        say(f"   [{'OK ' if needle in src else ' X '}] {_version} {label}")
    _unknown_counter_ok = ('_UNKNOWN_TODAY = [0, ""]' in src
                           and '_UNKNOWN_TODAY[2]' not in src
                           and '_UNKNOWN_TODAY[1] == today' in src)
    say(f"   [{'OK ' if _unknown_counter_ok else ' X '}] v1.9.12 unknown-signal retry counter fix")
    if not _unknown_counter_ok:
        problems.append("unknown-signal counter can break Telegram catch-up; use the V4.8.1 hotfix source")
    power_file = HERE / "SCREEN-OFF-KEEP-LAPTOP-ON.bat"
    power_text = power_file.read_text(encoding="utf-8", errors="replace") if power_file.exists() else ""
    power_ok = ("monitor-timeout-ac 5" in power_text
                and "standby-timeout-ac 0" in power_text
                and "standby-timeout-dc" not in power_text
                and "LIDACTION" not in power_text
                and "powercfg /hibernate off" not in power_text)
    say(f"   [{'OK ' if power_ok else ' X '}] v1.9.12 screen-off / plugged-in awake BAT")
    if not power_ok:
        problems.append("screen-off helper missing or it changes out-of-scope battery/lid/hibernate settings")

    say("-" * 74)
    for mod, pipname, label in (("MetaTrader5", "MetaTrader5", "MetaTrader5  (orders to MT5)"),
                                ("telethon", "telethon", "telethon     (Telegram login)"),
                                ("PIL", "Pillow", "Pillow       (Provider logo in PDF/Excel)"),
                                ("openpyxl", "openpyxl", "openpyxl    (editable Provider Excel exports)")): 
        try:
            __import__(mod)
            say(f"   [OK ] {label}")
        except Exception:
            say(f"   [ - ] {label}")
            say(f"          ->  install it with:   python -m pip install {pipname}")
            if mod == "PIL":
                say("          (Selected-logo exports need Pillow; the desktop export now shows the exact import failure.")
                say("           Rebuild with BUILD-EXE.bat, then use the complete dist/EdgeQuantSentinel folder.)")

    # ------------------------------------------------------------ verdict ---
    say("=" * 74)
    if not problems:
        say("   HARIYATA WADA KARANAWA  -  hama file ekakma aluth "
            f"(v{'.'.join(map(str, NEED))}).")
        say("   Now:  read SETUP.md  ->  EDGEQUANT-APP.bat  ->  TEST RUN")
        say("=" * 74)
        return 0
    say("   PURANA FILE EKA THIYENAWAA  -  meka hadanna:")
    for p in problems:
        say(f"     * {p}")
    say("")
    say("   HOW TO FIX (keep the old installation):")
    say("     1) Extract the NEW v1.9.12 ZIP into a NEW folder; do not replace the old folder.")
    say("     2) Close old EdgeQuant windows, then run EDGEQUANT-VERSION.bat in the new folder.")
    say("     3) Build the Windows EXE there with BUILD-EXE.bat.")
    say("=" * 74)
    return 1


if __name__ == "__main__":
    sys.exit(main())
