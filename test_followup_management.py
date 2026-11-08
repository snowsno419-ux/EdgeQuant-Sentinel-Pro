"""Offline tests for exact-entry Telegram follow-up management.

These tests never initialize MT5, send Telegram messages, or submit orders.
"""
import unittest
from unittest.mock import patch, Mock

import edgequant_auto as E


class FollowupManagementTests(unittest.TestCase):
    def setUp(self):
        self.rows = [
            {"chat_id": -10077, "message_id": 501, "ticket": 801,
             "source": "TEST LIMIT CHANNEL", "source_type": "LIMIT", "symbol": "XAUUSDm",
             "direction": "SELL", "sig_entry": 4013.0, "broker": "Broker A", "status": "pending"},
            {"chat_id": -10077, "message_id": 501, "ticket": 802,
             "source": "TEST LIMIT CHANNEL", "source_type": "LIMIT", "symbol": "XAUUSDm",
             "direction": "SELL", "sig_entry": 4013.0, "broker": "Broker A", "status": "pending"},
        ]

    def test_exact_channel_symbol_side_entry_groups_two_layers(self):
        result = E.match_followup_entry_records(
            "TEST LIMIT CHANNEL", -10077, "LIMIT", "XAUUSD", "SELL", 4013.0, self.rows)
        self.assertTrue(result["ok"])
        self.assertEqual(result["message_id"], 501)
        self.assertEqual(result["tickets_by_broker"], {"Broker A": [801, 802]})

    def test_wrong_chat_source_side_or_entry_fails_closed(self):
        for args in [
            ("TEST LIMIT CHANNEL", -10078, "LIMIT", "XAUUSD", "SELL", 4013.0),
            ("OTHER CHANNEL", -10077, "LIMIT", "XAUUSD", "SELL", 4013.0),
            ("TEST LIMIT CHANNEL", -10077, "LIMIT", "XAUUSD", "BUY", 4013.0),
            ("TEST LIMIT CHANNEL", -10077, "LIMIT", "XAUUSD", "SELL", 4013.1),
        ]:
            with self.subTest(args=args):
                result = E.match_followup_entry_records(*args, records=self.rows)
                self.assertFalse(result["ok"])

    def test_multiple_original_signal_ids_are_ambiguous(self):
        rows = self.rows + [dict(self.rows[0], message_id=502, ticket=803)]
        result = E.match_followup_entry_records(
            "TEST LIMIT CHANNEL", -10077, "LIMIT", "XAUUSD", "SELL", 4013.0, rows)
        self.assertFalse(result["ok"])
        self.assertIn("multiple original signal IDs", result["reason"])

    def test_closed_trade_is_not_a_target(self):
        rows = [dict(row, status="closed") for row in self.rows]
        result = E.match_followup_entry_records(
            "TEST LIMIT CHANNEL", -10077, "LIMIT", "XAUUSD", "SELL", 4013.0, rows)
        self.assertFalse(result["ok"])

    def test_followup_parser_requires_explicit_symbol_side_and_entry(self):
        text = "GOLD SELL 4013 BE now"
        parsed = E.parse_signal(text, default_order_type="LIMIT")
        update = E.parse_followup_management(text, parsed)
        self.assertEqual(update["action"], "move_be")
        self.assertEqual((update["symbol"], update["direction"], update["entries"]),
                         ("XAUUSD", "SELL", [4013.0]))

        broad = "All trades today BE (SL to entry) @ 30 pips profit"
        update = E.parse_followup_management(
            broad, E.parse_signal(broad, default_order_type="LIMIT"))
        self.assertEqual(update["action"], "move_be")
        self.assertEqual(update["entries"], [])
        self.assertEqual(update["direction"], "")

    def test_complete_new_signal_with_advisory_be_is_not_a_management_update(self):
        text = "GOLD SELL 4013 SL 4019 TP 4000 (or you can BE on 50 pips)"
        parsed = E.parse_signal(text, default_order_type="LIMIT")
        self.assertIsNone(E.parse_followup_management(text, parsed))

    def test_pending_order_tp_update_is_scoped_as_pending(self):
        text = "GOLD SELL 4013 set pending order TP 4000"
        parsed = E.parse_signal(text, default_order_type="LIMIT")
        update = E.parse_followup_management(text, parsed)
        self.assertEqual(update["action"], "modify_tp")
        self.assertEqual(update["scope"], "pending")
        self.assertEqual(update["entries"], [4013.0])

    def test_handler_journals_exact_intent_but_never_calls_mt5_when_unavailable(self):
        audit = Mock()
        journal = Mock(return_value=True)
        with patch.multiple(E, TRADES=self.rows, AUTO_BE_ENABLED=True,
                            AUTO_BE_PIPS=50, HAVE_MT5=False), \
             patch.object(E, "signal_message_is_new", return_value=True), \
             patch.object(E, "signal_audit_latest", return_value=None), \
             patch.object(E, "journal", journal), \
             patch.object(E, "signal_audit", audit), \
             patch.object(E, "signal_review_add") as review_add, \
             patch.object(E, "mt5_ready") as mt5_ready, \
             patch.object(E, "move_to_be") as move_to_be:
            E.handle_signal("GOLD SELL 4013 BE now", "TEST LIMIT CHANNEL", -10077,
                            "LIMIT", msg_id=901, msg_ts=1_800_000_000)
        self.assertTrue(any(call.kwargs.get("durable") for call in journal.call_args_list))
        self.assertEqual(audit.call_args.kwargs["outcome"], "blocked")
        review_add.assert_not_called()
        mt5_ready.assert_not_called()
        move_to_be.assert_not_called()

    def test_handler_sends_ambiguous_followup_to_review_without_intent(self):
        ambiguous = self.rows + [dict(self.rows[0], message_id=502, ticket=803)]
        journal = Mock(return_value=True)
        with patch.multiple(E, TRADES=ambiguous, HAVE_MT5=False), \
             patch.object(E, "signal_message_is_new", return_value=True), \
             patch.object(E, "signal_audit_latest", return_value=None), \
             patch.object(E, "journal", journal), \
             patch.object(E, "signal_audit") as audit, \
             patch.object(E, "signal_review_add") as review_add:
            E.handle_signal("GOLD SELL 4013 BE now", "TEST LIMIT CHANNEL", -10077,
                            "LIMIT", msg_id=902, msg_ts=1_800_000_001)
        self.assertTrue(review_add.called)
        self.assertEqual(audit.call_args.kwargs["outcome"], "needs_review")
        self.assertFalse(any(call.args and isinstance(call.args[0], dict) and
                             call.args[0].get("action") == "management_intent"
                             for call in journal.call_args_list))


if __name__ == "__main__":
    unittest.main()
