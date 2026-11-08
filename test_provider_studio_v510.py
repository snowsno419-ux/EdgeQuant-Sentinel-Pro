"""Offline V5.1 Provider reporting tests; no Telegram or MT5 connection is used."""
from __future__ import annotations

from datetime import datetime
from contextlib import closing
from pathlib import Path
import tempfile
import time
import unittest
import zipfile
from unittest.mock import patch

import edgequant_auto as E
import edgequant_desktop as desktop
import provider_studio as studio


class _Tree:
    def __init__(self):
        self.rows = {}

    def get_children(self):
        return tuple(self.rows)

    def delete(self, *children):
        for child in children:
            self.rows.pop(child, None)

    def insert(self, parent, index, iid=None, values=()):
        key = str(iid if iid is not None else len(self.rows))
        self.rows[key] = tuple(values)
        return key


class _Var:
    def __init__(self):
        self.value = ""

    def set(self, value):
        self.value = value


class ProviderStudioV510Tests(unittest.TestCase):
    @staticmethod
    def fixture(now=None):
        now = float(now if now is not None else time.time())
        publications = [
            {
                "id": "market-win", "created_ts": now - 3, "status": "CLOSED",
                "composer": {"symbol": "XAUUSD", "direction": "BUY", "order_type": "MARKET",
                             "entry": "4100", "sl": "4090", "tp_levels": [4101, 4110]},
                "progress_events": [{"label": "TP1 HIT", "revision": 1}],
                "targets": [{"id": -1001, "name": "Alpha Group"}],
                "local_trade_ids": ["trade-win"], "level_revision": 1,
            },
            {
                "id": "limit-loss", "created_ts": now - 2, "status": "SL HIT",
                "composer": {"symbol": "XAUUSD", "direction": "BUY", "order_type": "LIMIT",
                             "entry": "4100", "sl": "4090", "tp_levels": [4120]},
                "progress_events": [{"label": "SL HIT", "revision": 1}],
                "targets": [{"id": -1002, "name": "Beta Channel"}],
                "local_trade_ids": ["trade-loss"], "level_revision": 1,
            },
        ]
        trades = [
            {"id": "trade-win", "status": "closed", "net": 5.0, "symbol": "XAUUSD",
             "direction": "BUY", "open_price": 4100.0, "close_price": 4101.0},
            {"id": "trade-loss", "status": "closed", "net": -2.0, "symbol": "XAUUSD",
             "direction": "BUY", "open_price": 4100.0, "close_price": 4090.0},
        ]
        return publications, trades, now

    def test_signal_post_header_is_destination_specific(self):
        base = "📊 TRADE SIGNAL\nXAUUSD BUY\nENTRY: 2000"
        alpha = desktop.EdgeQuantApp._studio_signal_message_for_destination(base, "Alpha Group")
        beta = desktop.EdgeQuantApp._studio_signal_message_for_destination(base, "Beta Channel")
        self.assertEqual(alpha.splitlines()[0], "📊 Alpha Group • TRADE SIGNAL")
        self.assertEqual(beta.splitlines()[0], "📊 Beta Channel • TRADE SIGNAL")
        self.assertNotIn("Beta Channel", alpha)
        self.assertEqual(alpha.splitlines()[1:], base.splitlines()[1:])
        self.assertEqual(beta.splitlines()[1:], base.splitlines()[1:])

    def test_destination_exports_filter_signals_and_daily_pdf_includes_only_successful_sent_rows(self):
        from openpyxl import load_workbook

        publications, trades, now = self.fixture()
        # Model the real publication record, where a positive message ID means this target send succeeded.
        for row in publications:
            for target in row["targets"]:
                target["message_id"] = 500 + abs(int(target["id"]))
        brand = "Alpha Group"
        logo_path = Path(__file__).with_name("edgequant-logo-small.png")
        with tempfile.TemporaryDirectory(prefix="edgequant-destination-report-") as temp_dir:
            xlsx = Path(temp_dir) / "alpha.xlsx"
            pdf = Path(temp_dir) / "alpha.pdf"
            daily = Path(temp_dir) / "alpha-daily.pdf"
            daily_xlsx = Path(temp_dir) / "alpha-daily.xlsx"
            studio.export_provider_xlsx(
                xlsx, publications, trades, engine=E, logo_path=logo_path,
                provider_name=brand, destination_id=-1001, destination_name=brand)
            workbook = load_workbook(xlsx, read_only=False, data_only=True)
            try:
                self.assertEqual(workbook["SUMMARY"]["A1"].value, brand)
                self.assertEqual(workbook["SUMMARY"]["B5"].value, 1)
                destination_values = [workbook["DESTINATIONS"].cell(row, 1).value
                                      for row in range(2, workbook["DESTINATIONS"].max_row + 1)]
                self.assertIn("Alpha Group", destination_values)
                self.assertNotIn("Beta Channel", destination_values)
                signal_values = [workbook["SIGNALS"].cell(row, 3).value
                                 for row in range(4, workbook["SIGNALS"].max_row + 1)]
                self.assertEqual(signal_values, ["XAUUSD"])
                self.assertEqual(workbook["LINKED MT5 TRADES"]["A2"].value, "market-win")
                self.assertEqual(workbook["LINKED MT5 TRADES"]["C2"].value, "trade-win")
                for sheet in workbook.worksheets:
                    self.assertEqual(sheet.oddFooter.left.text, "EdgeQuant Sentinel")
            finally:
                workbook.close()
            studio.export_provider_pdf(
                pdf, publications, trades, engine=E, logo_path=logo_path,
                provider_name=brand, destination_id=-1001, destination_name=brand)
            daily_now = datetime.fromtimestamp(now).astimezone()
            daily_publications = [dict(row, targets=[dict(target) for target in row["targets"]])
                                  for row in publications]
            yesterday = dict(daily_publications[0], id="old-success", created_ts=now - 90000,
                             targets=[{"id": -1001, "name": brand, "message_id": 9001}])
            unsent = dict(daily_publications[0], id="failed-today", created_ts=now - 1,
                          targets=[{"id": -1001, "name": brand, "message_id": 0}])
            daily_publications.extend([yesterday, unsent])
            studio.export_provider_daily_pdf(
                daily, daily_publications, trades, engine=E, logo_path=logo_path,
                destination_id=-1001, destination_name=brand, now=daily_now)
            studio.export_provider_daily_xlsx(
                daily_xlsx, daily_publications, trades, engine=E, logo_path=logo_path,
                destination_id=-1001, destination_name=brand, now=daily_now)
            daily_book = load_workbook(daily_xlsx, read_only=False, data_only=True)
            try:
                self.assertEqual(daily_book["SUMMARY"]["A1"].value, brand)
                self.assertEqual(daily_book["SUMMARY"]["B5"].value, 1)
                self.assertIsNone(daily_book["SUMMARY"]["A6"].value)
                self.assertEqual(daily_book["SIGNALS"].max_row, 4)
                self.assertEqual(daily_book["DESTINATIONS"]["A2"].value, brand)
                self.assertEqual(daily_book["LINKED MT5 TRADES"]["A2"].value, "market-win")
                self.assertEqual(daily_book["LINKED MT5 TRADES"]["C2"].value, "trade-win")
                self.assertEqual(daily_book["SUMMARY"].oddFooter.left.text, "EdgeQuant Sentinel")
            finally:
                daily_book.close()
            for file in (pdf, daily):
                payload = file.read_bytes()
                self.assertIn(brand.encode("ascii"), payload)
                self.assertIn(b"EdgeQuant Sentinel", payload)
                self.assertIn(b"/Subtype /Image", payload)
                self.assertNotIn(b"Beta Channel", payload)
                self.assertIn(b"market-win", payload)
                self.assertIn(b"trade-win", payload)

    def test_provider_pdf_discloses_no_linked_trades_instead_of_fabricating_journal_rows(self):
        publications, _trades, now = self.fixture()
        logo_path = Path(__file__).with_name("edgequant-logo-small.png")
        with tempfile.TemporaryDirectory(prefix="edgequant-no-journal-") as temp_dir:
            pdf = Path(temp_dir) / "no-linked-journal.pdf"
            studio.export_provider_pdf(
                pdf, publications[:1], trades=[], engine=E, logo_path=logo_path,
                destination_id=-1001, destination_name="Alpha Group")
            payload = pdf.read_bytes()
            self.assertIn(b"No linked MT5 Trade Journal rows", payload)
            self.assertNotIn(b"trade-win", payload)

    def test_provider_manual_magic_zero_trade_link_flows_to_destination_report(self):
        from openpyxl import load_workbook

        publications, _trades, now = self.fixture()
        manual_id = "PROVIDER-MANUAL:DEMO:81234"
        signal = dict(publications[0], provider_manual_trade_ids=[manual_id], local_trade_ids=[])
        manual_trade = {"id": manual_id, "status": "closed", "result": "tp", "net": 7.25,
                        "symbol": "XAUUSD", "direction": "BUY", "open_price": 4100.0,
                        "close_price": 4101.0, "placed_ts": now - 10, "closed_ts": now - 5,
                        "magic": 0, "source": "PROVIDER MANUAL MT5 LINK", "ticket": 81234,
                        "broker": "DEMO"}
        rows = studio.provider_signal_rows([signal], [manual_trade], E)
        self.assertEqual(rows[0]["linked_trade_ids"], [manual_id])
        self.assertEqual(rows[0]["actual_trade_count"], 1)
        self.assertEqual(rows[0]["actual_net"], 7.25)
        with tempfile.TemporaryDirectory(prefix="edgequant-provider-manual-link-") as temp_dir:
            path = Path(temp_dir) / "alpha-linked.xlsx"
            studio.export_provider_xlsx(
                path, [signal], [manual_trade], engine=E,
                logo_path=Path(__file__).with_name("edgequant-logo-small.png"),
                destination_id=-1001, destination_name="Alpha Group")
            workbook = load_workbook(path, read_only=False, data_only=True)
            try:
                linked = workbook["LINKED MT5 TRADES"]
                self.assertEqual(linked["A2"].value, "market-win")
                self.assertEqual(linked["C2"].value, manual_id)
                self.assertEqual(linked["G2"].value, "XAUUSD")
            finally:
                workbook.close()

    def test_compiled_client_settings_persist_as_json_without_rewriting_python_source(self):
        import json
        import sys

        before = float(E.LAYER1_TP_PIPS)
        before_channels = dict(E.CHANNEL_IDS)
        try:
            with tempfile.TemporaryDirectory(prefix="edgequant-client-settings-") as temp_dir:
                path = Path(temp_dir) / "edgequant_user_settings.json"
                with patch.object(desktop, "CLIENT_SETTINGS_FILE", path), patch.object(sys, "frozen", True, create=True):
                    saved = desktop.save_settings_file(Path(temp_dir) / "edgequant_auto.py",
                        {"LAYER1_TP_PIPS": (35, "int"),
                         "CHANNEL_IDS": (["-1001: LIMIT"], "dict")})
                    data = json.loads(path.read_text(encoding="utf-8"))
                    self.assertEqual(saved, str(path))
                    self.assertEqual(data["values"]["LAYER1_TP_PIPS"], 35)
                    self.assertEqual(float(E.LAYER1_TP_PIPS), 35.0)
                    self.assertEqual(E.CHANNEL_IDS, {-1001: "LIMIT"})
                    self.assertFalse((Path(temp_dir) / "edgequant_auto.py").exists())
        finally:
            E.apply_desktop_settings({"LAYER1_TP_PIPS": before, "QUICK_TP_PIPS": before,
                                      "CHANNEL_IDS": before_channels},
                                     {"LAYER1_TP_PIPS": "float", "QUICK_TP_PIPS": "float",
                                      "CHANNEL_IDS": "dict"})

    def test_frozen_client_smoke_test_does_not_depend_on_source_files(self):
        app = object.__new__(desktop.EdgeQuantApp)
        with patch.object(desktop, "q_log") as logger:
            self.assertEqual(app._client_frozen_selftest(), 0)
        self.assertTrue(any("Layer 2 TP offset applied" in str(call) for call in logger.call_args_list))

    def test_provider_layer_one_override_is_independent_and_layer_two_signal_tp_is_shifted(self):
        global_l1 = float(E.LAYER1_TP_PIPS)
        sig = E.parse_signal("XAUUSD BUY\nSL 4090\nTP 4200", default_order_type="MARKET")
        plan = E.build_plan(sig, "MARKET", E.Broker(), 4100.0, 4099.8,
                            quick_tp_pips=25.0)
        self.assertEqual(len(plan), 2)
        self.assertAlmostEqual(float(plan[0]["tp"]), 4102.5)
        self.assertEqual(plan[0]["tag"], "quick25")
        self.assertEqual(float(plan[1]["tp"]), 4199.0)
        self.assertEqual(plan[1]["tag"], "tp1")
        # The Provider override must not mutate the Signal Receiver/global value.
        self.assertEqual(float(E.LAYER1_TP_PIPS), global_l1)

    def test_group_counts_include_market_limit_linked_trades_and_tp_sl(self):
        publications, trades, now = self.fixture()
        data = studio.provider_performance(publications, trades, E, now=now)
        groups = {row["destination"]: row for row in data["groups"]}
        self.assertEqual(set(groups), {"Alpha Group", "Beta Channel"})
        self.assertEqual(groups["Alpha Group"]["signals"], 1)
        self.assertEqual(groups["Alpha Group"]["market"], 1)
        self.assertEqual(groups["Alpha Group"]["actual_trades"], 1)
        self.assertEqual(groups["Alpha Group"]["wins"], 1)
        self.assertEqual(groups["Alpha Group"]["tp_hits"], 1)
        self.assertEqual(groups["Beta Channel"]["limit"], 1)
        self.assertEqual(groups["Beta Channel"]["actual_trades"], 1)
        self.assertEqual(groups["Beta Channel"]["losses"], 1)
        self.assertEqual(groups["Beta Channel"]["sl_hits"], 1)
        self.assertEqual(data["periods"]["today"]["wins"], 1)
        self.assertEqual(data["periods"]["today"]["losses"], 1)
        self.assertEqual(data["periods"]["today"]["best_signal"]["id"], "market-win")

    def test_desktop_today_group_and_live_tables_render_synthetic_snapshots(self):
        publications, trades, now = self.fixture()
        data = studio.provider_performance(publications, trades, E, now=now)
        probe = type("Probe", (), {})()
        probe.studio_today_tp_tree = _Tree()
        probe.studio_today_sl_tree = _Tree()
        probe.studio_destination_tree = _Tree()
        probe.studio_destination_summary_var = _Var()
        probe.studio_live_market_tree = _Tree()
        probe.studio_live_limit_tree = _Tree()
        probe.studio_live_summary_var = _Var()
        probe.mt5_info = {"brokers": [{"name": "B1", "currency": "USD"}]}
        other_magic = int(getattr(E, "MAGIC", 1) or 1) + 555
        probe.external_trade_snapshot = {
            "status": "connected", "updated_ts": now,
            "manage_rows": [
                {"kind": "OPEN", "state": "LIVE", "magic": 0, "broker": "B1",
                 "ticket": 101, "symbol": "XAUUSD", "direction": "BUY", "entry": 4100.0,
                 "current": 4102.0, "market_price": 4102.0, "sl": 4090.0, "tp": 4110.0,
                 "pl": 3.5, "opened_ts": now - 60, "source": "MT5 Manual / External"},
                {"kind": "PENDING", "state": "PENDING", "order_kind": "LIMIT", "magic": 0,
                 "broker": "B1", "ticket": 102, "symbol": "XAUUSD", "direction": "SELL",
                 "entry": 4104.0, "current": 4102.0, "market_price": 4102.0,
                 "sl": 4110.0, "tp": 4090.0, "opened_ts": 0, "source": "Manual"},
                {"kind": "PENDING", "state": "PENDING", "order_kind": "LIMIT", "magic": other_magic,
                 "broker": "B1", "ticket": 103, "symbol": "XAUUSD", "direction": "BUY",
                 "entry": 4099.0, "current": 4102.0, "market_price": 4102.0,
                 "sl": 4090.0, "tp": 4110.0, "opened_ts": 0, "source": "Other EA"},
            ],
        }

        desktop.EdgeQuantApp._studio_refresh_today_signal_lists(probe, data)
        desktop.EdgeQuantApp._studio_refresh_group_performance(probe, data)
        desktop.EdgeQuantApp._studio_refresh_live_orders(probe)

        self.assertEqual(len(probe.studio_today_tp_tree.rows), 1)
        self.assertEqual(len(probe.studio_today_sl_tree.rows), 1)
        self.assertEqual(len(probe.studio_destination_tree.rows), 2)
        self.assertIn("linked closed MT5 trades: 2", probe.studio_destination_summary_var.value)
        market = next(iter(probe.studio_live_market_tree.rows.values()))
        limit = next(iter(probe.studio_live_limit_tree.rows.values()))
        self.assertEqual(len(probe.studio_live_market_tree.rows), 1)
        self.assertEqual(len(probe.studio_live_limit_tree.rows), 1)
        self.assertEqual(market[9], "+20.0")
        self.assertEqual(limit[7], "20.0")
        self.assertIn("USD +3.50", probe.studio_live_summary_var.value)
        self.assertIn("Open market: 1", probe.studio_live_summary_var.value)
        self.assertIn("Pending LIMIT: 1", probe.studio_live_summary_var.value)

    def test_provider_report_brand_title_logo_and_edgequant_footer(self):
        from openpyxl import load_workbook

        publications, trades, _now = self.fixture()
        brand = "Aurora Signals"
        logo_path = Path(__file__).with_name("edgequant-logo-small.png")
        with tempfile.TemporaryDirectory(prefix="edgequant-provider-brand-") as temp_dir:
            xlsx = Path(temp_dir) / "provider.xlsx"
            pdf = Path(temp_dir) / "provider.pdf"
            studio.export_provider_xlsx(xlsx, publications, trades, engine=E,
                                        logo_path=logo_path, provider_name=brand)
            book = load_workbook(xlsx, read_only=False, data_only=True)
            try:
                self.assertEqual(book.properties.title, f"{brand} Provider Performance")
                self.assertEqual(book["SUMMARY"]["A1"].value, brand)
                self.assertEqual(book["SUMMARY"].oddFooter.left.text, "EdgeQuant Sentinel")
                for sheet in book.worksheets:
                    self.assertEqual(sheet.oddFooter.left.text, "EdgeQuant Sentinel")
            finally:
                book.close()
            studio.export_provider_pdf(pdf, publications, trades, engine=E,
                                       logo_path=logo_path, provider_name=brand)
            payload = pdf.read_bytes()
            self.assertIn(brand.encode("ascii"), payload)
            self.assertIn(b"EdgeQuant Sentinel", payload)
            with zipfile.ZipFile(xlsx, "r") as archive:
                self.assertIsNone(archive.testzip())
                self.assertTrue(any(name.startswith("xl/media/") for name in archive.namelist()))

    def test_eod_recipients_are_successfully_sent_signal_destinations_today_only(self):
        now = 1_800_000_000.0
        start = now - 86400.0
        publications = [
            {"created_ts": now - 120, "targets": [
                {"id": -1001, "name": "Alpha Group", "message_id": 17},
                {"id": -1002, "name": "No ID Channel", "message_id": 0}]},
            {"created_ts": now - 60, "targets": [
                {"id": -1001, "name": "Alpha Group", "message_id": 18}]},
            {"created_ts": start - 1, "targets": [
                {"id": -1003, "name": "Yesterday Group", "message_id": 19}]},
        ]
        rows = desktop.EdgeQuantApp._studio_successful_signal_destinations(publications, start, now)
        self.assertEqual(rows, [{"id": -1001, "name": "Alpha Group", "signals": 2}])

    def test_logo_pillow_import_error_preserves_actionable_diagnostic(self):
        import builtins

        logo_path = Path(__file__).with_name("edgequant-logo-small.png")
        real_import = builtins.__import__

        def fail_pillow_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name == "PIL":
                raise ImportError("synthetic Pillow loader failure")
            return real_import(name, globals, locals, fromlist, level)

        with patch("builtins.__import__", side_effect=fail_pillow_import):
            with self.assertRaises(RuntimeError) as raised:
                studio._logo_assets(logo_path)
        self.assertIn("Import diagnostic: ImportError: synthetic Pillow loader failure", str(raised.exception))
        self.assertIn("rebuild the complete folder", str(raised.exception))
        self.assertIn("dist/EdgeQuantSentinel", str(raised.exception))

    def test_invalid_logo_has_pillow_decode_diagnostic(self):
        with tempfile.TemporaryDirectory(prefix="edgequant-invalid-logo-") as temp_dir:
            logo_path = Path(temp_dir) / "broken.png"
            logo_path.write_bytes(b"not an image")
            with self.assertRaises(RuntimeError) as raised:
                studio._logo_assets(logo_path)
        self.assertIn("could not be decoded by Pillow", str(raised.exception))
        self.assertIn("Image diagnostic:", str(raised.exception))
        self.assertIn("BUILD-EXE.bat", str(raised.exception))

    def test_excel_provider_report_exports_best_destination_and_trade_counts(self):
        from openpyxl import load_workbook

        publications, trades, _now = self.fixture()
        with tempfile.TemporaryDirectory(prefix="edgequant-provider-v510-") as temp_dir:
            path = Path(temp_dir) / "provider.xlsx"
            logo_path = Path(__file__).with_name("edgequant-logo-small.png")
            studio.export_provider_xlsx(path, publications, trades, engine=E,
                                        logo_path=logo_path, provider_name="Offline Test")
            with zipfile.ZipFile(path, "r") as archive:
                self.assertIsNone(archive.testzip())
                self.assertTrue(any(name.startswith("xl/media/") for name in archive.namelist()),
                                "Provider Excel export did not embed the bundled logo")
            # Windows cannot delete this XLSX while openpyxl's read-only ZIP
            # archive is still open. unittest.addCleanup runs *after* the
            # TemporaryDirectory context exits, which is too late on Windows.
            with closing(load_workbook(path, read_only=True, data_only=True)) as workbook:
                self.assertIn("DESTINATIONS", workbook.sheetnames)
                self.assertIn("SIGNALS", workbook.sheetnames)
                self.assertIn("BEST SIGNAL", [cell.value for cell in workbook["SUMMARY"][4]])
                destinations = workbook["DESTINATIONS"]
                header = [cell.value for cell in destinations[1]]
                self.assertIn("LINKED MT5 TRADES", header)
                actual_col = header.index("LINKED MT5 TRADES") + 1
                destination_col = header.index("DESTINATION") + 1
                counts = {destinations.cell(row, destination_col).value:
                          destinations.cell(row, actual_col).value for row in range(2, destinations.max_row + 1)}
                self.assertEqual(counts["Alpha Group"], 1)
                self.assertEqual(counts["Beta Channel"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
